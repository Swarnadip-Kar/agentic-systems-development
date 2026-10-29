"""Lab 7a: the runtime harness, aider-assisted -- builds directly on
Lab 6b's native tool-calling loop (given here as finished code) and
Week 7's lecture. Pull the loop apart: a pure step function that only
decides what to do next, and a RuntimeHarness that owns the step
budget, the wall-clock timeout, structured trace logging, and error
isolation."""
import json
import os
import time
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError

MAX_AGENT_STEPS = 12
DEFAULT_TIMEOUT_SECONDS = 60

TICKETS_STATUS = {}  # populated by load_ticket_statuses() in main()
CLOSED_TICKETS = []
ASSIGNMENTS = {}
ESCALATIONS = []

TICKET_HISTORY = {
    1: ["created", "assigned to agent_a"],
    2: ["created", "assigned to agent_b", "resolved by agent_b"],
    3: ["created"],
    4: ["created", "assigned to agent_a", "reassigned to agent_c"],
    5: ["created", "resolved by agent_a"],
    6: ["created", "escalated once already"],
}

GRANTED_READ_ONLY = {"read"}
GRANTED_FULL = {"read", "write"}

# Three canned situations run_scenarios (Exercise 5) drives through the
# harness -- one that should finish normally, one where a tool is
# deliberately broken, and one with a step budget too small to finish.
SCENARIOS = [
    {
        "name": "normal",
        "task": "Check the status of ticket 1.",
        "max_steps": MAX_AGENT_STEPS,
        "break_tool": None,
    },
    {
        "name": "broken_tool",
        "task": "Escalate ticket 4 with a short reason.",
        "max_steps": MAX_AGENT_STEPS,
        "break_tool": "escalate_ticket",
    },
    {
        "name": "exhausted",
        "task": "Find all unresolved tickets and escalate any older than 3 days, with a short reason.",
        "max_steps": 1,
        "break_tool": None,
    },
]


def load_ticket_statuses():
    data = json.loads(Path(__file__).with_name("tickets_status.json").read_text())
    return {row["id"]: {"status": row["status"], "age_days": row["age_days"]} for row in data}


def get_client():
    return OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )


def call_with_retry(client, **kwargs):
    for attempt in range(4):
        try:
            return client.chat.completions.create(**kwargs)
        except (RateLimitError, APIError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def check_ticket_status(ticket_id):
    return TICKETS_STATUS.get(ticket_id, {"error": "no such ticket"})


def escalate_ticket(ticket_id, reason):
    ESCALATIONS.append({"ticket_id": ticket_id, "reason": reason})
    return {"escalated": True, "ticket_id": ticket_id}


def search_tickets(status):
    return [tid for tid, t in TICKETS_STATUS.items() if t["status"] == status]


def reassign_ticket(ticket_id, assignee):
    ASSIGNMENTS[ticket_id] = assignee
    return {"reassigned": True, "ticket_id": ticket_id, "assignee": assignee}


def close_ticket(ticket_id):
    CLOSED_TICKETS.append(ticket_id)
    return {"closed": True, "ticket_id": ticket_id}


def get_ticket_history(ticket_id):
    return TICKET_HISTORY.get(ticket_id, {"error": "no such ticket"})


_TYPE_MAP = {"integer": int, "string": str, "boolean": bool, "number": (int, float)}


def validate_arguments(schema, arguments):
    """Given, unchanged from Lab 6a."""
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for field in required:
        if field not in arguments:
            return False, f"missing required field: {field}"
    for field, value in arguments.items():
        if field in properties:
            expected_type = properties[field].get("type")
            py_type = _TYPE_MAP.get(expected_type)
            if py_type and not isinstance(value, py_type):
                return False, f"field '{field}' expected {expected_type}, got {type(value).__name__}"
    return True, None


# Lab 6b's registry, given here as finished.
TOOL_REGISTRY = {
    "check_ticket_status": {
        "fn": check_ticket_status,
        "description": "Look up a ticket's status and age.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
        "permission": "read",
    },
    "escalate_ticket": {
        "fn": escalate_ticket,
        "description": "Escalate a ticket with a reason.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["ticket_id", "reason"],
        },
        "permission": "write",
    },
    "search_tickets": {
        "fn": search_tickets,
        "description": "List ticket ids matching a status.",
        "parameters": {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
        },
        "permission": "read",
    },
    "reassign_ticket": {
        "fn": reassign_ticket,
        "description": "Reassign a ticket to a new agent.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer"},
                "assignee": {"type": "string"},
            },
            "required": ["ticket_id", "assignee"],
        },
        "permission": "write",
    },
    "close_ticket": {
        "fn": close_ticket,
        "description": "Close a ticket.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
        "permission": "write",
    },
    "get_ticket_history": {
        "fn": get_ticket_history,
        "description": "Get a ticket's history of past actions.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
        "permission": "read",
    },
}


def build_native_tools(registry):
    """Given, unchanged from Lab 6b."""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"],
            },
        }
        for name, spec in registry.items()
    ]


def dispatch_native_tool_call(tool_call, registry, granted_permissions):
    """Given, unchanged from Lab 6b. Note what it does NOT catch: a tool
    that raises anything other than TypeError propagates straight up to
    whoever called it."""
    name = tool_call.function.name
    if name not in registry:
        return {"error": f"unknown tool: {name}"}
    spec = registry[name]
    if spec["permission"] not in granted_permissions:
        return {"error": f"permission denied: '{name}' requires '{spec['permission']}' permission"}
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        return {"error": f"invalid arguments JSON: {e}"}
    valid, error = validate_arguments(spec["parameters"], arguments)
    if not valid:
        return {"error": f"invalid arguments: {error}"}
    try:
        return spec["fn"](**arguments)
    except TypeError as e:
        return {"error": f"dispatch failed: {e}"}


def registry_with_broken_tool(registry, tool_name):
    """Given -- a shallow copy of `registry` where `tool_name`'s function
    raises RuntimeError, standing in for a real dependency being down.
    Used by SCENARIOS["broken_tool"]."""
    def broken(**kwargs):
        raise RuntimeError(f"{tool_name} service is down")
    copy = {name: dict(spec) for name, spec in registry.items()}
    copy[tool_name]["fn"] = broken
    return copy


def agent_step(state, client, registry, tools, granted_permissions):
    response = client.chat.completions.create(model="main", messages=state["messages"], tools=tools, tool_choice="auto")
    message = response.choices[0].message

    if response.choices[0].finish_reason != "tool_calls":
        return (state, True, message.content)

    new_messages = state["messages"] + [{
        "role": "assistant",
        "content": message.content,
        "tool_calls": [tc.model_dump() for tc in message.tool_calls]
    }]

    step_output = []
    for tool_call in message.tool_calls:
        result = dispatch_native_tool_call(tool_call, registry, granted_permissions)
        new_messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })
        step_output.append({
            "tool": tool_call.function.name,
            "result": result
        })

    return ({"messages": new_messages}, False, step_output)


class RuntimeHarness:
    def __init__(self, max_steps=MAX_AGENT_STEPS, timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
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
            elapsed = time.monotonic() - start
            if elapsed > self.timeout_seconds:
                self._log({"step": step, "elapsed_s": round(elapsed, 2), "status": "timeout"})
                return {"status": "timeout", "steps_taken": step - 1, "elapsed_s": round(elapsed, 2)}

            try:
                new_state, done, output = agent_step_fn(state)
                self._log({"step": step, "elapsed_s": round(elapsed, 2), "status": "ok", "output": output})
                if done:
                    return {"status": "done", "steps_taken": step, "output": output}
                state = new_state
            except Exception as e:
                self._log({"step": step, "elapsed_s": round(elapsed, 2), "status": "error", "error": f"{type(e).__name__}: {e}"})
                return {"status": "error", "steps_taken": step, "error": f"{type(e).__name__}: {e}"}

        return {"status": "exhausted", "steps_taken": self.max_steps}


def read_trace(trace_path):
    entries = []
    with open(trace_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def trace_summary(entries):
    total = len(entries)
    by_status = {}
    total_elapsed_s = 0.0

    for entry in entries:
        status = entry.get("status")
        if status:
            by_status[status] = by_status.get(status, 0) + 1
        elapsed_s = entry.get("elapsed_s", 0.0)
        total_elapsed_s += elapsed_s

    avg_elapsed_s = total_elapsed_s / total if total > 0 else 0.0
    last_status = entries[-1]["status"] if entries else None

    return {
        "total": total,
        "by_status": by_status,
        "avg_elapsed_s": avg_elapsed_s,
        "last_status": last_status
    }


def run_scenarios(client, registry, granted_permissions, trace_dir="."):
    results = []
    for scenario in SCENARIOS:
        name = scenario["name"]
        task = scenario["task"]
        max_steps = scenario["max_steps"]
        break_tool = scenario["break_tool"]

        current_registry = registry_with_broken_tool(registry, break_tool) if break_tool else registry
        tools = build_native_tools(current_registry)

        trace_path = f"{trace_dir}/harness_trace_{name}.jsonl"
        with open(trace_path, "w") as f:
            f.close()

        harness = RuntimeHarness(max_steps=max_steps, trace_path=trace_path)
        state = {"messages": [{"role": "user", "content": task}]}

        result = harness.run(lambda state: agent_step(state, client, current_registry, tools, granted_permissions), state)

        print(f"{name}: status={result['status']} steps_taken={result['steps_taken']}")
        summary = trace_summary(read_trace(trace_path))
        print(summary)

        results.append({
            "name": name,
            "result": result,
            "summary": summary
        })

    return results


def main():
    global TICKETS_STATUS
    TICKETS_STATUS = load_ticket_statuses()
    client = get_client()

    run_scenarios(client, TOOL_REGISTRY, GRANTED_FULL)


if __name__ == "__main__":
    main()
