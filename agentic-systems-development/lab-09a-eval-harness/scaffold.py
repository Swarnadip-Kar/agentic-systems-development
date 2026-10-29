"""Lab 9a: an evaluation harness for your own agent -- aider-assisted.
Builds on Week 9's lecture. Your Lab 8a planner, the ReAct step, Week 7's
RuntimeHarness and the ticket tools are all given as finished code. You
build the tests around them: answers written first, checks, a run of the
whole test set, and a comparison."""
import collections
import json
import os
import threading
import time
from pathlib import Path

import openai

MAX_ROUNDS = 10
DEFAULT_TIMEOUT_SECONDS = 180
RATE_LIMIT_RPM = 28  # every gateway key allows 30 calls a minute
TEMPERATURE = 0      # used by both patterns; see the README's optional extra

GRANTED_FULL = {"read", "write"}

# --- the ticket world: one fresh copy per run -------------------------------

def load_tickets():
    rows = json.loads(Path(__file__).with_name("tickets.json").read_text())
    return {row["id"]: row for row in rows}


class TicketWorld:
    def __init__(self):
        rows = load_tickets()
        self.tickets = {tid: {"status": r["status"], "age_days": r["age_days"]}
                        for tid, r in rows.items()}
        self.history = {tid: list(r["history"]) for tid, r in rows.items()}
        self.escalations = []

    def search_tickets(self, status):
        return sorted(tid for tid, t in self.tickets.items() if t["status"] == status)

    def check_ticket_status(self, ticket_id):
        return self.tickets.get(ticket_id, {"error": "no such ticket"})

    def get_ticket_history(self, ticket_id):
        if ticket_id not in self.history:
            return {"error": "no such ticket"}
        return {"ticket_id": ticket_id, "history": self.history[ticket_id]}

    def escalate_ticket(self, ticket_id, reason):
        if ticket_id not in self.tickets:
            return {"error": "no such ticket"}
        self.escalations.append({"ticket_id": ticket_id, "reason": reason})
        return {"escalated": True, "ticket_id": ticket_id}

    def escalated_ids(self):
        return sorted(e["ticket_id"] for e in self.escalations)


def build_registry(world):
    return {
        "search_tickets": {
            "fn": world.search_tickets,
            "description": "List the ids of tickets with a given status.",
            "parameters": {"type": "object", "properties": {"status": {"type": "string"}},
                           "required": ["status"]},
            "permission": "read",
        },
        "check_ticket_status": {
            "fn": world.check_ticket_status,
            "description": "Look up a ticket's status and age in days.",
            "parameters": {"type": "object", "properties": {"ticket_id": {"type": "integer"}},
                           "required": ["ticket_id"]},
            "permission": "read",
        },
        "get_ticket_history": {
            "fn": world.get_ticket_history,
            "description": "Get a ticket's history of past actions.",
            "parameters": {"type": "object", "properties": {"ticket_id": {"type": "integer"}},
                           "required": ["ticket_id"]},
            "permission": "read",
        },
        "escalate_ticket": {
            "fn": world.escalate_ticket,
            "description": "Escalate a ticket to tier 2 with a one-line reason.",
            "parameters": {"type": "object",
                           "properties": {"ticket_id": {"type": "integer"},
                                          "reason": {"type": "string"}},
                           "required": ["ticket_id", "reason"]},
            "permission": "write",
        },
    }


# --- registry plumbing, as in Labs 6 and 7 ---------------------------------

_TYPE_MAP = {"integer": int, "string": str, "boolean": bool, "number": (int, float)}


def validate_arguments(schema, arguments):
    for field in schema.get("required", []):
        if field not in arguments:
            return False, f"missing required field: {field}"
    for field, value in arguments.items():
        expected = schema.get("properties", {}).get(field, {}).get("type")
        py_type = _TYPE_MAP.get(expected)
        if py_type and not isinstance(value, py_type):
            return False, f"field '{field}' expected {expected}, got {type(value).__name__}"
    return True, None


def build_native_tools(registry):
    return [{"type": "function",
             "function": {"name": name, "description": spec["description"],
                          "parameters": spec["parameters"]}}
            for name, spec in registry.items()]


def describe_tools(registry):
    lines = []
    for name, spec in registry.items():
        params = ", ".join(f"{p}: {v['type']}" for p, v in spec["parameters"]["properties"].items())
        lines.append(f"- {name}({params}): {spec['description']}")
    return "\n".join(lines)


def dispatch(name, arguments, registry, granted_permissions):
    """Permission check, then schema check, then the call. Never raises."""
    if name not in registry:
        return {"error": f"unknown tool: {name}"}
    spec = registry[name]
    if spec["permission"] not in granted_permissions:
        return {"error": f"permission denied: '{name}' requires '{spec['permission']}' permission"}
    valid, error = validate_arguments(spec["parameters"], arguments)
    if not valid:
        return {"error": f"invalid arguments: {error}"}
    try:
        return spec["fn"](**arguments)
    except TypeError as e:
        return {"error": f"dispatch failed: {e}"}


# --- the model client ----------------------------------------------------------

def get_client():
    # max_retries=0: the SDK would otherwise wait out a rate limit silently
    # inside what looks like one slow call. CountingClient retries itself.
    return openai.OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )


class _Pacer:
    def __init__(self):
        self.starts = collections.deque()
        self.lock = threading.Lock()

    def wait_for_slot(self):
        while True:
            with self.lock:
                now = time.monotonic()
                while self.starts and now - self.starts[0] >= 60:
                    self.starts.popleft()
                if len(self.starts) < RATE_LIMIT_RPM:
                    self.starts.append(now)
                    return
                pause = 60 - (now - self.starts[0]) + 0.05
            time.sleep(pause)


_PACER = _Pacer()


class _CountingCompletions:
    def __init__(self, outer):
        self.outer = outer

    def create(self, **kwargs):
        self.outer.calls += 1
        for attempt in range(4):
            _PACER.wait_for_slot()
            try:
                return self.outer.inner.chat.completions.create(**kwargs)
            except openai.RateLimitError as e:
                if attempt == 3:
                    raise
                time.sleep(float(e.response.headers.get("retry-after", "10")))


class _CountingChat:
    def __init__(self, outer):
        self.completions = _CountingCompletions(outer)


class CountingClient:
    """Wraps a client. Counts model calls in .calls, and keeps under the
    gateway's rate limit. Use one per run."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0
        self.chat = _CountingChat(self)


# --- Week 7's harness, unchanged -------------------------------------------

class RuntimeHarness:
    def __init__(self, max_steps=MAX_ROUNDS, timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                 trace_path="harness_trace.jsonl"):
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.trace_path = trace_path

    def _log(self, entry):
        with open(self.trace_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def run(self, agent_step_fn, state):
        start = time.monotonic()
        for step in range(1, self.max_steps + 1):
            elapsed = round(time.monotonic() - start, 2)
            if elapsed > self.timeout_seconds:
                self._log({"step": step, "elapsed_s": elapsed, "status": "timeout"})
                return {"status": "timeout", "steps_taken": step - 1, "elapsed_s": elapsed}
            try:
                state, done, output = agent_step_fn(state)
            except Exception as e:
                elapsed = round(time.monotonic() - start, 2)
                err = f"{type(e).__name__}: {e}"
                self._log({"step": step, "elapsed_s": elapsed, "status": "error", "error": err})
                return {"status": "error", "steps_taken": step, "error": err}
            elapsed = round(time.monotonic() - start, 2)
            self._log({"step": step, "elapsed_s": elapsed, "status": "ok", "output": output})
            if done:
                return {"status": "done", "steps_taken": step, "output": output}
        return {"status": "exhausted", "steps_taken": self.max_steps}


def read_trace(trace_path):
    with open(trace_path) as f:
        return [json.loads(line) for line in f if line.strip()]


# --- the lecture's ReAct step: the baseline you compare against -------------

REACT_SYSTEM = "You are a support-ticket agent. Use the tools to complete the task."


def react_initial_state(task):
    return {"messages": [{"role": "system", "content": REACT_SYSTEM},
                         {"role": "user", "content": task}]}


def react_step(state, client, registry, granted_permissions):
    response = client.chat.completions.create(
        model="main", temperature=TEMPERATURE, messages=state["messages"],
        tools=build_native_tools(registry), tool_choice="auto",
    )
    choice = response.choices[0]
    message = choice.message
    if choice.finish_reason != "tool_calls":
        return state, True, message.content
    new_messages = state["messages"] + [{
        "role": "assistant", "content": message.content,
        "tool_calls": [tc.model_dump() for tc in message.tool_calls],
    }]
    step_output = []
    for tool_call in message.tool_calls:
        try:
            arguments = json.loads(tool_call.function.arguments or "{}")
        except json.JSONDecodeError as e:
            arguments, result = {}, {"error": f"invalid arguments JSON: {e}"}
        else:
            result = dispatch(tool_call.function.name, arguments, registry, granted_permissions)
        step_output.append({"tool": tool_call.function.name, "arguments": arguments, "result": result})
        new_messages.append({"role": "tool", "tool_call_id": tool_call.id,
                             "content": json.dumps(result)})
    return {"messages": new_messages}, False, step_output


# --- the planner's prompt ------------------------------------------------------

PLANNER_RULES = (
    "Rules:\n"
    "- Use only literal argument values you have actually seen in the results so far. "
    "Never write placeholders or references to earlier steps.\n"
    "- If a call needs a value you have not seen yet, end the plan before that call. "
    "You will be shown the results and asked to plan again.\n"
    "- Never repeat a call that already succeeded.\n"
    "- Include only the calls the task actually needs.\n"
    "- Set done to true, with no steps, only when every part of the task is finished."
)


def plan_initial_state(task):
    return {"task": task, "observations": []}


def planner_messages(task, observations, registry):
    system = ("You plan work for a support-ticket agent, a few tool calls at a time.\n\n"
              "Tools:\n" + describe_tools(registry) + "\n\n" + PLANNER_RULES)
    seen = json.dumps(observations, indent=1) if observations else "none yet"
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Task: {task}\n\nResults so far:\n{seen}"}]


# --- your Lab 8a planner, given back as finished code -----------------------

def build_plan_schema(registry):
    return {
        "type": "object",
        "properties": {
            "done": {"type": "boolean"},
            "steps": {"type": "array", "items": {
                "type": "object",
                "properties": {"tool": {"type": "string", "enum": list(registry)},
                               "arguments": {"type": "object"}},
                "required": ["tool", "arguments"]}},
        },
        "required": ["done", "steps"],
    }


def cut_before_unobserved_writes(plan, registry):
    seen_read = False
    for i, step in enumerate(plan):
        permission = registry.get(step["tool"], {}).get("permission")
        if permission == "write" and seen_read:
            return list(plan[:i])
        if permission == "read":
            seen_read = True
    return list(plan)


def execute_until_stuck(plan, registry, granted_permissions):
    observations = []
    for step in plan:
        result = dispatch(step["tool"], step["arguments"], registry, granted_permissions)
        if isinstance(result, dict) and str(result.get("error", "")).startswith("invalid arguments"):
            observations.append({"not_run": step["tool"], "why": (
                f"{result['error']}. It was never executed. Plan this call again using "
                "real values from the results above.")})
            break
        observations.append({"tool": step["tool"], "arguments": step["arguments"], "result": result})
    return observations


def plan_decision(state, client, registry):
    """One planning call. Returns the parsed {"done": ..., "steps": [...]}."""
    response = client.chat.completions.create(
        model="main", temperature=TEMPERATURE,
        messages=planner_messages(state["task"], state["observations"], registry),
        response_format={"type": "json_schema",
                         "json_schema": {"name": "plan", "schema": build_plan_schema(registry)}},
    )
    return json.loads(response.choices[0].message.content)


def plan_execute_step(state, client, registry, granted_permissions):
    """Your Lab 8a Exercise 4: one planning round as a step function."""
    decision = plan_decision(state, client, registry)
    if decision["done"]:
        return state, True, "planner: done"
    if not decision["steps"]:
        new = [{"not_run": "anything", "why": "You said the task is not done but planned no steps."}]
    else:
        new = execute_until_stuck(cut_before_unobserved_writes(decision["steps"], registry),
                                  registry, granted_permissions)
    return {"task": state["task"], "observations": state["observations"] + new}, False, new


# The two versions of the agent this lab evaluates:
# name -> (step function, initial state from the task text).
PATTERNS = {
    "react": (react_step, react_initial_state),
    "plan-execute": (plan_execute_step, plan_initial_state),
}


# --- your work ---------------------------------------------------------------

def load_test_set(path="test_set.json"):
    with open(path) as f:
        cases = json.load(f)
    
    case_ids = set()
    for case in cases:
        if 'id' not in case:
            raise ValueError("Case is missing 'id'")
        if 'task' not in case:
            raise ValueError(f"Case with id {case['id']} is missing 'task'")
        if 'history_before_escalate' not in case:
            raise ValueError(f"Case with id {case['id']} is missing 'history_before_escalate'")
        if 'expected_escalations' not in case:
            raise ValueError(f"Case with id {case['id']} is missing 'expected_escalations'")
        if not isinstance(case['expected_escalations'], list):
            raise ValueError(f"Case with id {case['id']} has non-list 'expected_escalations'")
        if not all(isinstance(e, int) for e in case['expected_escalations']):
            raise ValueError(f"Case with id {case['id']} has non-integer 'expected_escalations'")
        if case['id'] in case_ids:
            raise ValueError(f"Duplicate case id: {case['id']}")
        case_ids.add(case['id'])
        case['expected_escalations'].sort()
    
    return cases


def check_outcome(case, world, result):
    if result["status"] != "done":
        return False, f"run ended with status {result['status']}"
    if world.escalated_ids() != case['expected_escalations']:
        return False, f"escalated {world.escalated_ids()}, expected {case['expected_escalations']}"
    return True, "ok"


def check_process(case, trace):
    if not case['history_before_escalate']:
        return True, "not required"
    
    history_read = {}
    for entry in trace:
        output = entry.get('output')
        if not isinstance(output, list):
            continue
        for item in output:
            if item.get('tool') == 'get_ticket_history':
                ticket_id = item['arguments']['ticket_id']
                if 'error' not in item['result']:
                    # Only Set on First Read
                    if ticket_id not in history_read:
                        history_read[ticket_id] = entry['step']
    
    for entry in trace:
        output = entry.get('output')
        if not isinstance(output, list):
            continue
        for item in output:
            if item.get('tool') == 'escalate_ticket' and item['result'].get('escalated'):
                ticket_id = item['arguments']['ticket_id']
                if ticket_id not in history_read or history_read[ticket_id] >= entry['step']:
                    return False, f"escalated ticket {ticket_id} in step {entry['step']} before its history had been read"
    
    return True, "ok"


def run_test_set(client, cases, patterns=("react", "plan-execute"), runs=1, trace_dir="."):
    rows = []
    for case in cases:
        case_id = case['id']
        for pattern in patterns:
            for run in range(1, runs + 1):
                world = TicketWorld()
                registry = build_registry(world)
                counting_client = CountingClient(client)
                trace_path = f"{trace_dir}/trace_{case_id}_{pattern}_{run}.jsonl"
                Path(trace_path).unlink(missing_ok=True) # delete file if it exists
                harness = RuntimeHarness(max_steps=MAX_ROUNDS, timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                                        trace_path=trace_path)
                
                # 1. Standard function definition
                def step_fn(st):
                    return PATTERNS[pattern][0](st, counting_client, registry, GRANTED_FULL)

                # 2. Pass step_fn into harness.run
                result = harness.run(step_fn, PATTERNS[pattern][1](case['task']))
                
                outcome_ok, outcome_detail = check_outcome(case, world, result)
                process_ok, process_detail = check_process(case, read_trace(harness.trace_path))
                passed = outcome_ok and process_ok
                detail = "; ".join([f"outcome: {outcome_detail}", f"process: {process_detail}"]) if not passed else "ok"
                rows.append({
                    "case": case_id,
                    "pattern": pattern,
                    "run": run,
                    "status": result["status"],
                    "calls": counting_client.calls,
                    "outcome_ok": outcome_ok,
                    "process_ok": process_ok,
                    "passed": passed,
                    "detail": detail
                })
    return rows


def compare_report(rows, cases):
    summary = {pattern: {} for pattern in PATTERNS}
    for case in cases:
        case_id = case['id']
        for pattern in PATTERNS:
            pattern_data = [row for row in rows if row['case'] == case_id and row['pattern'] == pattern]
            passed_runs = sum(row['passed'] for row in pattern_data)
            mean_calls = round(sum(row['calls'] for row in pattern_data) / len(pattern_data), 1) if pattern_data else 0
            summary[pattern][case_id] = {
                "passed": passed_runs,
                "runs": len(pattern_data),
                "mean_calls": mean_calls
            }
    
    for case in cases:
        case_id = case['id']
        print(f"Case {case_id}:")
        for pattern in PATTERNS:
            pattern_data = summary[pattern][case_id]
            print(f"  {pattern:<13} {pattern_data['passed']}/{pattern_data['runs']} runs, mean calls {pattern_data['mean_calls']:.1f}")
    
    for pattern in PATTERNS:
        total_passed = sum(summary[pattern][case_id]['passed'] for case_id in summary[pattern])
        total_runs = sum(summary[pattern][case_id]['runs'] for case_id in summary[pattern])
        total_mean_calls = sum(summary[pattern][case_id]['mean_calls'] * summary[pattern][case_id]['runs'] for case_id in summary[pattern]) / total_runs if total_runs > 0 else 0
        print(f"Total {pattern}: {total_passed}/{total_runs} runs, mean calls {total_mean_calls:.1f}")


def main():
    cases = load_test_set()
    rows = run_test_set(get_client(), cases)
    compare_report(rows, cases)
    for row in rows:
        if not row["passed"]:
            print(f"  {row['pattern']:<13} {row['case']:<26} run {row['run']}: {row['detail']}")


if __name__ == "__main__":
    main()
