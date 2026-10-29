"""Lab 8a: plan, execute, replan -- aider-assisted. Builds directly on
Week 8's lecture. Week 7's RuntimeHarness, the ticket tools and their
registry, dispatch, and the lecture's ReAct step are all given as
finished code. You build the planner-executor pattern around them."""
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

GRANTED_FULL = {"read", "write"}

# The tasks compare_patterns runs, each with its right answer written down first.
TASKS = [
    {
        "id": "escalate-never-escalated",
        "task": "Find all unresolved tickets and escalate every one that has never been "
                "escalated before. Give a one-line reason for each escalation.",
        "expected_escalations": [23, 42],
    },
    {
        "id": "known-path",
        "task": "Escalate tickets 23 and 42, each with the reason 'older than 3 days and "
                "never escalated'.",
        "expected_escalations": [23, 42],
    },
    {
        "id": "older-than-six-days",
        "task": "Escalate every unresolved ticket that is older than 6 days and has never "
                "been escalated before.",
        "expected_escalations": [23],
    },
]


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
        model="main", temperature=0, messages=state["messages"],
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


# --- your work ---------------------------------------------------------------

def build_plan_schema(registry):
    tool_names = list(registry.keys())
    return {
        "type": "object",
        "properties": {
            "done": {"type": "boolean"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tool": {"type": "string", "enum": tool_names},
                        "arguments": {"type": "object"}
                    },
                    "required": ["tool", "arguments"]
                }
            }
        },
        "required": ["done", "steps"]
    }


def cut_before_unobserved_writes(plan, registry):
    read_occurred = False
    new_plan = []
    for step in plan:
        tool = step.get("tool")
        if tool in registry:
            if registry[tool]["permission"] == "write":
                if read_occurred:
                    break
            elif registry[tool]["permission"] == "read":
                read_occurred = True
        new_plan.append(step)
    return new_plan


def execute_until_stuck(plan, registry, granted_permissions):
    observations = []
    for step in plan:
        tool = step.get("tool")
        arguments = step.get("arguments")
        result = dispatch(tool, arguments, registry, granted_permissions)
        if "error" in result:
            if result["error"].startswith("invalid arguments"):
                observations.append({"not_run": tool, "why": f"{result['error']}. It was never executed. Plan this call again using real values from the results above."})
                break
            else:
                observations.append({"tool": tool, "arguments": arguments, "result": result})
        else:
            observations.append({"tool": tool, "arguments": arguments, "result": result})
    return observations


def plan_execute_step(state, client, registry, granted_permissions):
    task = state["task"]
    observations = state["observations"]

    response = client.chat.completions.create(
        model="main",
        temperature=0,
        messages=planner_messages(task, observations, registry),
        response_format={"type": "json_schema", "json_schema": {"name": "plan", "schema": build_plan_schema(registry)}}
    )

    try:
        plan = response.choices[0].message.content
        plan = json.loads(plan)
    except (json.JSONDecodeError, KeyError):
        return state, False, [{"not_run": "anything", "why": "Failed to parse the plan from the response."}]

    if plan.get("done"):
        return state, True, "planner: done"

    steps = plan.get("steps", [])
    if not steps:
        new_observation = {"not_run": "anything", "why": "You said the task is not done but planned no steps."}
        new_state = {"task": task, "observations": observations + [new_observation]}
        return new_state, False, [new_observation]

    filtered_plan = cut_before_unobserved_writes(steps, registry)
    new_observations = execute_until_stuck(filtered_plan, registry, granted_permissions)

    new_state = {"task": task, "observations": observations + new_observations}
    return new_state, False, new_observations


def compare_patterns(client, tasks=TASKS, runs=1, trace_dir="."):
    rows = []
    for task in tasks:
        task_id = task["id"]
        for pattern in ["react", "plan-execute"]:
            for run in range(1, runs + 1):
                world = TicketWorld()
                registry = build_registry(world)
                counting_client = CountingClient(client)
                trace_path = f"{trace_dir}/trace_{task_id}_{pattern}_{run}.jsonl"
                with open(trace_path, "w") as f:
                    pass  # Start the trace file empty

                harness = RuntimeHarness(max_steps=MAX_ROUNDS, trace_path=trace_path)
                if pattern == "react":
                    initial_state = react_initial_state(task["task"])
                    step_fn = lambda state: react_step(state, counting_client, registry, GRANTED_FULL)
                elif pattern == "plan-execute":
                    initial_state = plan_initial_state(task["task"])
                    step_fn = lambda state: plan_execute_step(state, counting_client, registry, GRANTED_FULL)

                result = harness.run(step_fn, initial_state)
                status = result["status"]
                escalated = world.escalated_ids()
                calls = counting_client.calls
                correct = status == "done" and escalated == sorted(task["expected_escalations"])

                row = {
                    "task": task_id,
                    "pattern": pattern,
                    "run": run,
                    "status": status,
                    "escalated": escalated,
                    "calls": calls,
                    "correct": correct
                }
                rows.append(row)
                print(row)

    return rows


def main():
    compare_patterns(get_client())


if __name__ == "__main__":
    main()
