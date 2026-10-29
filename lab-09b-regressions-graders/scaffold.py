"""Lab 9b: regressions and grading the grader -- aider-assisted. Builds on
Lab 9a, whose evaluation harness is given here as finished code, and on
Week 9's lecture. You check a change for regressions, label answers
yourself, write a grader, and measure the grader against your labels."""
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


def plan_decision(state, client, registry, model="main"):
    """One planning call. Returns the parsed {"done": ..., "steps": [...]}."""
    response = client.chat.completions.create(
        model=model, temperature=TEMPERATURE,
        messages=planner_messages(state["task"], state["observations"], registry),
        response_format={"type": "json_schema",
                         "json_schema": {"name": "plan", "schema": build_plan_schema(registry)}},
    )
    return json.loads(response.choices[0].message.content)


def plan_execute_step(state, client, registry, granted_permissions, model="main"):
    """Your Lab 8a Exercise 4: one planning round as a step function."""
    decision = plan_decision(state, client, registry, model)
    if decision["done"]:
        return state, True, "planner: done"
    if not decision["steps"]:
        new = [{"not_run": "anything", "why": "You said the task is not done but planned no steps."}]
    else:
        new = execute_until_stuck(cut_before_unobserved_writes(decision["steps"], registry),
                                  registry, granted_permissions)
    return {"task": state["task"], "observations": state["observations"] + new}, False, new


# The versions of the agent this lab evaluates:
# name -> (step function, initial state from the task text).
PATTERNS = {
    "react": (react_step, react_initial_state),
    "plan-execute": (plan_execute_step, plan_initial_state),
    # The change this lab tests: the same planner on the smaller aux model.
    "plan-execute-on-aux": (lambda state, client, registry, granted:
                            plan_execute_step(state, client, registry, granted, model="aux"),
                            plan_initial_state),
}


# --- your Lab 9a evaluation harness, given back as finished code ---------------

def load_test_set(path="test_set.json"):
    cases = json.loads(Path(path).read_text())
    seen = set()
    for case in cases:
        cid = case.get("id")
        for key in ("id", "task", "history_before_escalate"):
            if key not in case:
                raise ValueError(f"case {cid}: missing {key}")
        expected = case.get("expected_escalations")
        if not isinstance(expected, list) or not all(
                isinstance(t, int) and not isinstance(t, bool) for t in expected):
            raise ValueError(f"case {cid}: expected_escalations must be a list of ticket ids")
        if cid in seen:
            raise ValueError(f"case {cid}: duplicate id")
        seen.add(cid)
        case["expected_escalations"] = sorted(expected)
    return cases


def check_outcome(case, world, result):
    if result["status"] != "done":
        return False, f"run ended with status {result['status']}"
    got, expected = world.escalated_ids(), case["expected_escalations"]
    if got != expected:
        return False, f"escalated {got}, expected {expected}"
    return True, "ok"


def check_process(case, trace):
    if not case["history_before_escalate"]:
        return True, "not required"
    read_at = {}
    for entry in trace:
        if not isinstance(entry.get("output"), list):
            continue
        for call in entry["output"]:
            if "tool" not in call:
                continue
            tid = (call.get("arguments") or {}).get("ticket_id")
            result = call.get("result")
            if call["tool"] == "get_ticket_history" and isinstance(result, dict) and "error" not in result:
                read_at.setdefault(tid, entry["step"])
            if call["tool"] == "escalate_ticket" and isinstance(result, dict) and result.get("escalated"):
                if tid not in read_at or read_at[tid] >= entry["step"]:
                    return False, (f"escalated ticket {tid} in step {entry['step']} "
                                   "before its history had been read")
    return True, "ok"


def run_test_set(client, cases, patterns=("react", "plan-execute"), runs=1, trace_dir="."):
    rows = []
    for case in cases:
        for pattern in patterns:
            step_fn, initial_state = PATTERNS[pattern]
            for run in range(1, runs + 1):
                world = TicketWorld()
                registry = build_registry(world)
                counting = CountingClient(client)
                path = f"{trace_dir}/trace_{case['id']}_{pattern}_{run}.jsonl"
                open(path, "w").close()
                harness = RuntimeHarness(max_steps=MAX_ROUNDS, trace_path=path)
                result = harness.run(
                    lambda st, f=step_fn, c=counting, r=registry: f(st, c, r, GRANTED_FULL),
                    initial_state(case["task"]))
                outcome_ok, outcome_detail = check_outcome(case, world, result)
                process_ok, process_detail = check_process(case, read_trace(path))
                failures = ([f"outcome: {outcome_detail}"] if not outcome_ok else []) + \
                           ([f"process: {process_detail}"] if not process_ok else [])
                rows.append({"case": case["id"], "pattern": pattern, "run": run,
                             "status": result["status"], "calls": counting.calls,
                             "outcome_ok": outcome_ok, "process_ok": process_ok,
                             "passed": outcome_ok and process_ok,
                             "detail": "; ".join(failures) if failures else "ok"})
    return rows


def compare_report(rows, cases):
    summary = {}
    for row in rows:
        cell = summary.setdefault(row["pattern"], {}).setdefault(
            row["case"], {"passed": 0, "runs": 0, "calls": 0})
        cell["passed"] += row["passed"]
        cell["runs"] += 1
        cell["calls"] += row["calls"]
    for by_case in summary.values():
        for cell in by_case.values():
            cell["mean_calls"] = round(cell.pop("calls") / cell["runs"], 1)
    patterns = list(summary)
    print(f"{'case':<26}" + "".join(f"{p:>22}" for p in patterns))
    for case in cases:
        cells = [summary[p].get(case["id"]) for p in patterns]
        print(f"{case['id']:<26}" + "".join(
            (f"{c['passed']}/{c['runs']}  {c['mean_calls']} calls" if c else "-").rjust(22) for c in cells))
    print(f"{'TOTAL':<26}" + "".join(
        (f"{sum(c['passed'] for c in summary[p].values())}/"
         f"{sum(c['runs'] for c in summary[p].values())}").rjust(22) for p in patterns))
    return summary


# --- the runbook answers and the grader's prompt ----------------------------------

def load_runbook():
    return json.loads(Path(__file__).with_name("runbook.json").read_text())


RUNBOOK = load_runbook()


def grader_messages(item, rubric):
    """The two messages a grader sees: your rubric, then the runbook, the
    question, and the answer to grade."""
    runbook = "\n".join(f"[{doc_id}] {text}" for doc_id, text in RUNBOOK.items())
    return [{"role": "system", "content": "You are a strict grader for a support team.\n\n" + rubric},
            {"role": "user", "content": (f"Runbook:\n{runbook}\n\nQuestion: {item['question']}"
                                         f"\n\nAnswer to grade: {item['answer']}")}]


# Exercise 4: write your grading rubric here.
RUBRIC = """
Grade the answer against the runbook ONLY. Check each:
1. Every claim in the answer is supported by the runbook (no contradictions).
2. The answer adds no facts, numbers, or steps the runbook does not state.
3. The answer addresses the question, or says plainly that the runbook does not cover it.
Verdict is "pass" only if ALL three hold. If any fails, verdict is "fail".
Give a one-line reason naming the failed criterion.
"""


# --- your work ---------------------------------------------------------------

def build_verdict_schema():
    return {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["pass", "fail"]},
            "reason": {"type": "string"},
            "relevant": {"type": "boolean"},
            "accurate": {"type": "boolean"},
            "concise": {"type": "boolean"}
        },
        "required": ["verdict", "reason"]
    }


def grade_answer(item, client, model):
    response = client.chat.completions.create(
        model=model, temperature=0, messages=grader_messages(item, RUBRIC),
        response_format={"type": "json_schema",
                         "json_schema": {"name": "grade", "schema": build_verdict_schema()}}
    )
    return json.loads(response.choices[0].message.content)


def grade_the_graders(client, answers, labels, graders=("aux", "main")):
    results = {}
    for grader in graders:
        counting = CountingClient(client)
        agree = 0
        disagreements = []
        verdicts = {}

        for item in answers:                      # list, in file order
            answer_id = item["id"]
            verdict = grade_answer(item, counting, grader)["verdict"]
            verdicts[answer_id] = verdict
            if verdict == labels.get(answer_id):
                agree += 1
            else:
                disagreements.append(answer_id)

        results[grader] = {"agree": agree, "total": len(answers),
                           "disagreements": disagreements}
        print(f"{grader} agreement: {agree}/{len(answers)}")
        for d in disagreements:
            print(f"Disagreement: {d}, grader: {verdicts[d]}, your label: {labels.get(d)}")
    return results


def regression_check(summary, cases, baseline, candidate):
    regressions = []
    for case in cases:
        baseline_passed = summary.get(baseline, {}).get(case["id"], {}).get("passed", 0)
        baseline_runs = summary.get(baseline, {}).get(case["id"], {}).get("runs", 1)
        candidate_passed = summary.get(candidate, {}).get(case["id"], {}).get("passed", 0)
        candidate_runs = summary.get(candidate, {}).get(case["id"], {}).get("runs", 1)
        if candidate_passed / candidate_runs < baseline_passed / baseline_runs:
            regressions.append(case["id"])
    return regressions


def run_regression(client, cases, baseline="plan-execute", candidate="plan-execute-on-aux", runs=1, trace_dir="."):
    rows = run_test_set(client, cases, patterns=(baseline, candidate), runs=runs, trace_dir=trace_dir)
    summary = compare_report(rows, cases)
    regressions = regression_check(summary, cases, baseline, candidate)
    
    for case in cases:
        baseline_passed = summary.get(baseline, {}).get(case["id"], {}).get("passed", 0)
        baseline_runs = summary.get(baseline, {}).get(case["id"], {}).get("runs", 1)
        candidate_passed = summary.get(candidate, {}).get(case["id"], {}).get("passed", 0)
        candidate_runs = summary.get(candidate, {}).get(case["id"], {}).get("runs", 1)
        
        baseline_rate = f"{baseline_passed}/{baseline_runs}"
        candidate_rate = f"{candidate_passed}/{candidate_runs}"
        
        if case["id"] in regressions:
            print(f"{case['id']} {baseline_rate} {candidate_rate} REGRESSION")
        else:
            print(f"{case['id']} {baseline_rate} {candidate_rate} ok")
    
    num_regressions = len(regressions)
    if num_regressions > 0:
        print(f"{num_regressions} cases got worse. Do not ship this change.")
    else:
        print("No regressions detected.")
    
    return {"summary": summary, "regressions": regressions}


def load_labels(path="answers.json"):
    items = json.loads(Path(path).read_text())
    labels = {}
    for item in items:
        answer_id = item.get("id")
        label = item.get("label")
        reason = item.get("reason")
        if label not in ("pass", "fail"):
            raise ValueError(f"answer {answer_id}: label must be 'pass' or 'fail', got {label!r}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"answer {answer_id}: reason is empty")
        labels[answer_id] = label
    return labels


def main():
    client = get_client()
    print("== Is the change safe? (planner on main vs on aux)")
    run_regression(client, load_test_set())
    print("\n== Does the grader agree with you?")
    answers = json.loads(Path(__file__).with_name("answers.json").read_text())
    grade_the_graders(client, answers, load_labels())


if __name__ == "__main__":
    main()
