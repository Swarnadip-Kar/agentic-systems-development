"""Lab 7b: bounding the unboundable, aider-assisted -- builds directly on
Lab 7a's runtime harness (given here as finished code) and Week 7's
lecture. Lab 7a's timeout only checks the clock BETWEEN steps; a step
that hangs is never caught. This lab adds three bounds at three
different places -- the model call, the whole step, and the individual
tool call -- and measures what each one lets the agent keep."""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError, APITimeoutError

MAX_AGENT_STEPS = 12
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MODEL_CALL_TIMEOUT = 30
DEFAULT_TOOL_TIMEOUT = 5

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

# The scenarios compare_harnesses (Exercise 5) runs through all three
# configurations. The second one wires in a tool that sleeps far longer
# than the harness timeout -- the exact situation Lab 7a's harness cannot
# recover from.
COMPARE_SCENARIOS = [
    {
        "name": "normal",
        "task": "Check the status of ticket 1.",
        "timeout_seconds": 30,
        "hang_tool": None,
        "hang_seconds": 0,
        "tool_timeout_seconds": 1,
    },
    {
        "name": "hanging_tool",
        "task": "Check the status of ticket 1.",
        "timeout_seconds": 8,
        "hang_tool": "check_ticket_status",
        "hang_seconds": 12,
        "tool_timeout_seconds": 1,
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
    """Given, unchanged from Lab 6b."""
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


def registry_with_hanging_tool(registry, tool_name, seconds):
    """Given -- a shallow copy of `registry` where `tool_name` sleeps for
    `seconds` before answering. Stands in for blocking I/O that never
    comes back: a stuck file read, a socket with no read timeout, a
    subprocess that never exits."""
    original = registry[tool_name]["fn"]

    def hanging(**kwargs):
        time.sleep(seconds)
        return original(**kwargs)

    copy = {name: dict(spec) for name, spec in registry.items()}
    copy[tool_name]["fn"] = hanging
    return copy


def agent_step_with_timeout(state, client, registry, tools, granted_permissions, model_call_timeout=DEFAULT_MODEL_CALL_TIMEOUT):
    """Given -- Lab 7a's pure step function, unchanged. Note there is no
    timeout on the model call here."""
    response = client.chat.completions.create(
        model="main", messages=state["messages"], tools=tools, tool_choice="auto", timeout=model_call_timeout
    )
    choice = response.choices[0]
    message = choice.message
    if choice.finish_reason != "tool_calls":
        return state, True, message.content

    new_messages = state["messages"] + [{
        "role": "assistant",
        "content": message.content,
        "tool_calls": [tc.model_dump() for tc in message.tool_calls],
    }]
    step_output = []
    for tool_call in message.tool_calls:
        result = dispatch_with_timeout(tool_call, registry, granted_permissions)
        step_output.append({"tool": tool_call.function.name, "result": result})
        new_messages.append({
            "role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result),
        })
    return {"messages": new_messages}, False, step_output


class RuntimeHarness:
    """Given -- Lab 7a's cooperative harness, unchanged. Its timeout is
    checked once per iteration, before agent_step_fn is called."""

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
    """Given, unchanged from Lab 7a."""
    with open(trace_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def trace_summary(entries):
    """Given, unchanged from Lab 7a."""
    by_status = {}
    for e in entries:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    avg = sum(e["elapsed_s"] for e in entries) / len(entries) if entries else 0.0
    return {
        "total": len(entries),
        "by_status": by_status,
        "avg_elapsed_s": avg,
        "last_status": entries[-1]["status"] if entries else None,
    }


def dispatch_with_timeout(tool_call, registry, granted_permissions, tool_timeout=DEFAULT_TOOL_TIMEOUT):
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(dispatch_native_tool_call, tool_call, registry, granted_permissions)
    try:
        result = future.result(timeout=tool_timeout)
    except FutureTimeoutError:
        name = tool_call.function.name
        return {"error": f"tool '{name}' timed out after {tool_timeout}s"}
    return result


def agent_step_with_tool_timeout(state, client, registry, tools, granted_permissions, tool_timeout=DEFAULT_TOOL_TIMEOUT):
    response = client.chat.completions.create(
        model="main", messages=state["messages"], tools=tools, tool_choice="auto"
    )
    choice = response.choices[0]
    message = choice.message
    if choice.finish_reason != "tool_calls":
        return state, True, message.content

    new_messages = state["messages"] + [{
        "role": "assistant",
        "content": message.content,
        "tool_calls": [tc.model_dump() for tc in message.tool_calls],
    }]
    step_output = []
    for tool_call in message.tool_calls:
        result = dispatch_with_timeout(tool_call, registry, granted_permissions, tool_timeout)
        step_output.append({"tool": tool_call.function.name, "result": result})
        new_messages.append({
            "role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result),
        })
    return {"messages": new_messages}, False, step_output


class PreemptiveRuntimeHarness(RuntimeHarness):
    def __init__(self, max_steps=MAX_AGENT_STEPS, timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                 trace_path="harness_trace.jsonl"):
        super().__init__(max_steps, timeout_seconds, trace_path)
        self.pool = ThreadPoolExecutor(max_workers=1)

    def _log(self, entry):
        super()._log(entry)

    def run(self, agent_step_fn, state):
        start = time.monotonic()
        for step in range(1, self.max_steps + 1):
            remaining = self.timeout_seconds - (time.monotonic() - start)
            if remaining <= 0:
                self._log({"step": step, "elapsed_s": round(time.monotonic() - start, 2), "status": "timeout"})
                return {"status": "timeout", "steps_taken": step - 1}
            future = self.pool.submit(agent_step_fn, state)
            try:
                state, done, output = future.result(timeout=remaining)
            except FutureTimeoutError:
                self._log({"step": step, "elapsed_s": round(time.monotonic() - start, 2), "status": "step_hung"})
                return {"status": "timeout", "steps_taken": step - 1, "elapsed_s": round(time.monotonic() - start, 2), "note": "step exceeded the deadline and was abandoned, not killed"}
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


def run_and_exit(harness, agent_step_fn, state):
    result = harness.run(agent_step_fn, state)
    print(json.dumps(result))
    sys.stdout.flush()
    os._exit(0)


def compare_harnesses(client, registry, granted_permissions, scenarios=COMPARE_SCENARIOS,
                      trace_dir="."):
    results = []
    for scenario in scenarios:
        name = scenario["name"]
        task = scenario["task"]
        timeout_seconds = scenario["timeout_seconds"]
        hang_tool = scenario["hang_tool"]
        hang_seconds = scenario["hang_seconds"]
        tool_timeout_seconds = scenario["tool_timeout_seconds"]

        if hang_tool:
            current_registry = registry_with_hanging_tool(registry, hang_tool, hang_seconds)
        else:
            current_registry = registry

        tools = build_native_tools(current_registry)

        state = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": task},
            ]
        }

        # Cooperative
        cooperative_trace_path = f"{trace_dir}/harness_trace_{name}_cooperative.jsonl"
        with open(cooperative_trace_path, "w") as f:
            pass  # Truncate the file
        cooperative_harness = RuntimeHarness(timeout_seconds=timeout_seconds, trace_path=cooperative_trace_path)
        start_time = time.monotonic()
        cooperative_result = cooperative_harness.run(lambda state: agent_step_with_timeout(state, client, current_registry, tools, granted_permissions), state)
        cooperative_elapsed = round(time.monotonic() - start_time, 2)
        cooperative_respected = cooperative_elapsed <= timeout_seconds + 1.0

        # Preemptive
        preemptive_trace_path = f"{trace_dir}/harness_trace_{name}_preemptive.jsonl"
        with open(preemptive_trace_path, "w") as f:
            pass  # Truncate the file
        preemptive_harness = PreemptiveRuntimeHarness(timeout_seconds=timeout_seconds, trace_path=preemptive_trace_path)
        start_time = time.monotonic()
        preemptive_result = preemptive_harness.run(lambda state: agent_step_with_timeout(state, client, current_registry, tools, granted_permissions), state)
        preemptive_elapsed = round(time.monotonic() - start_time, 2)
        preemptive_respected = preemptive_elapsed <= timeout_seconds + 1.0

        # Tool Bounded
        tool_bounded_trace_path = f"{trace_dir}/harness_trace_{name}_tool_bounded.jsonl"
        with open(tool_bounded_trace_path, "w") as f:
            pass  # Truncate the file
        tool_bounded_harness = RuntimeHarness(timeout_seconds=timeout_seconds, trace_path=tool_bounded_trace_path)
        start_time = time.monotonic()
        tool_bounded_result = tool_bounded_harness.run(lambda s: agent_step_with_tool_timeout(s, client, current_registry, tools, granted_permissions, tool_timeout_seconds), state)
        tool_bounded_elapsed = round(time.monotonic() - start_time, 2)
        tool_bounded_respected = tool_bounded_elapsed <= timeout_seconds + 1.0

        # Print results
        print(f"Scenario: {name}")
        print(f"  Cooperative: status={cooperative_result['status']}, elapsed_s={cooperative_elapsed}, respected_deadline={cooperative_respected}")
        print(f"  Preemptive: status={preemptive_result['status']}, elapsed_s={preemptive_elapsed}, respected_deadline={preemptive_respected}")
        print(f"  Tool Bounded: status={tool_bounded_result['status']}, elapsed_s={tool_bounded_elapsed}, respected_deadline={tool_bounded_respected}")

        # Append to results
        results.append({
            "name": name,
            "cooperative": {
                "status": cooperative_result["status"],
                "elapsed_s": cooperative_elapsed,
                "respected_deadline": cooperative_respected
            },
            "preemptive": {
                "status": preemptive_result["status"],
                "elapsed_s": preemptive_elapsed,
                "respected_deadline": preemptive_respected
            },
            "tool_bounded": {
                "status": tool_bounded_result["status"],
                "elapsed_s": tool_bounded_elapsed,
                "respected_deadline": tool_bounded_respected
            }
        })

    # Aggregate results
    cooperative_respected_count = sum(1 for r in results if r["cooperative"]["respected_deadline"])
    preemptive_respected_count = sum(1 for r in results if r["preemptive"]["respected_deadline"])
    tool_bounded_respected_count = sum(1 for r in results if r["tool_bounded"]["respected_deadline"])

    print(f"\nAggregate Results:")
    print(f"  Cooperative: respected deadline in {cooperative_respected_count}/{len(results)} scenarios")
    print(f"  Preemptive: respected deadline in {preemptive_respected_count}/{len(results)} scenarios")
    print(f"  Tool Bounded: respected deadline in {tool_bounded_respected_count}/{len(results)} scenarios")

    return results


def main():
    global TICKETS_STATUS
    TICKETS_STATUS = load_ticket_statuses()
    client = get_client()

    compare_harnesses(client, TOOL_REGISTRY, GRANTED_FULL)

    # A step abandoned by the preemptive harness is still running in a
    # background thread, and Python waits for it before the interpreter
    # is allowed to exit -- so a plain end-of-script would sit here for
    # the rest of the hang. Flush, then exit now.
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
