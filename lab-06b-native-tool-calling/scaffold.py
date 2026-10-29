"""Lab 6b: native tool calling, aider-assisted -- builds directly on
Lab 6a's registry (given here as finished, working code) and Lab 5b's
permission model. Points the exact same registry at real tools=/
tool_choice="auto" native function calling instead of the hand-rolled
prompt-and-parse loop."""
import json
import os
import time

from openai import OpenAI, APIError, RateLimitError
from pathlib import Path

MAX_AGENT_STEPS = 12

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

AGENT_TASKS = [
    "Check the status of ticket 1.",
    "Check ticket 4. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Find all unresolved tickets and escalate any older than 3 days, with a short reason.",
    "Which ticket has been open longer: ticket 2 or ticket 5? Answer with the ticket ID and its age in days.",
    "Reassign ticket 3 to agent bhupesh.",
]

GRANTED_READ_ONLY = {"read"}
GRANTED_FULL = {"read", "write"}


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


# Lab 6a's registry, given here as finished -- every tool now also
# carries a permission (Lab 5b), same field, same registry, no third
# structure.
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

def build_tools_desc(registry):
    tools_description = "You have the following tools available:\n"
    for tool_name, tool_info in registry.items():
        params = tool_info["parameters"].get("properties", {})
        param_str = ", ".join(f"{param}: {params[param]['type']}" for param in params)
        tools_description += f"{tool_name}({param_str}) -- {tool_info['description']}\n"
    
    tools_description += (
        "\nAt each turn respond with ONLY a JSON object, no other text, in one "
        "of these shapes:\n"
        '{"action": "call_tool", "tool": "check_ticket_status", '
        '"arguments": {"ticket_id": <int>}}\n'
        '{"action": "call_tool", "tool": "escalate_ticket", '
        '"arguments": {"ticket_id": <int>, "reason": "<str>"}}\n'
        '{"action": "final_answer", "answer": "<your answer>"}'
    )
    
    return tools_description

def dispatch_tool_call(decision, registry):
    """Given, unchanged from Lab 6a -- the hand-rolled path, no
    permission check (that was Lab 5b's harness, not this one)."""
    if decision.tool not in registry:
        return {"error": f"unknown tool: {decision.tool}"}
    spec = registry[decision.tool]
    valid, error = validate_arguments(spec["parameters"], decision.arguments)
    if not valid:
        return {"error": f"invalid arguments: {error}"}
    try:
        return spec["fn"](**decision.arguments)
    except TypeError as e:
        return {"error": f"dispatch failed: {e}"}


class _HandRolledDecision:
    """Given -- the shape run_agent_loop below expects, matching
    Lab 5a/6a's AgentDecision closely enough for dispatch_tool_call."""
    def __init__(self, action, tool=None, arguments=None, answer=None):
        self.action = action
        self.tool = tool
        self.arguments = arguments
        self.answer = answer


def _parse_hand_rolled_decision(raw_response_text):
    import re
    text = re.sub(r"^```json\s*|```\s*$", "", raw_response_text.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"response was not valid JSON: {e}"
    if data.get("action") not in ("call_tool", "final_answer"):
        return None, "action must be 'call_tool' or 'final_answer'"
    return _HandRolledDecision(**data), None


def _build_tools_desc(registry):
    lines = []
    for name, spec in registry.items():
        props = spec["parameters"]["properties"]
        params_str = ", ".join(f"{k}: {v['type']}" for k, v in props.items())
        lines.append(f"{name}({params_str}) -- {spec['description']}")
    return (
        "You have these tools:\n" + "\n".join(lines) + "\n\n"
        "At each turn respond with ONLY a JSON object, no other text, in "
        "one of these shapes:\n"
        '{"action": "call_tool", "tool": "<tool name>", "arguments": {...}}\n'
        '{"action": "final_answer", "answer": "<your answer>"}'
    )


def run_agent_loop(client, task, registry, max_steps=MAX_AGENT_STEPS):
    """Given -- Lab 6a's hand-rolled loop, unchanged. compare_traces
    (Exercise 4) runs this side by side with run_native_loop."""
    tools_desc = _build_tools_desc(registry)
    messages = [
        {"role": "system", "content": tools_desc},
        {"role": "user", "content": task},
    ]
    steps = []
    for step in range(max_steps):
        response = call_with_retry(client, model="main", messages=messages)
        raw = response.choices[0].message.content
        decision, error = _parse_hand_rolled_decision(raw)
        if error:
            messages.append({"role": "user", "content": f"Error: {error}. Respond with valid JSON."})
            continue

        messages.append({"role": "assistant", "content": raw})

        if decision.action == "final_answer":
            return {"task": task, "steps": steps, "final_answer": decision.answer, "steps_taken": step + 1}

        result = dispatch_tool_call(decision, registry)
        steps.append({"tool": decision.tool, "result": result})
        messages.append({"role": "user", "content": f"Tool result: {json.dumps(result)}"})

    return {"task": task, "steps": steps, "final_answer": None, "steps_taken": max_steps}


def build_native_tools(registry):
    tools = []
    for tool_name, tool_info in registry.items():
        params = tool_info["parameters"].get("properties", {})
        tool_params = [{"name": param, "type": params[param]["type"]} for param in params]
        tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_info["description"],
                "parameters": {
                    "type": "object",
                    "properties": {param: {"type": params[param]["type"]} for param in params},
                    "required": list(params.keys()),
                }
            }
        })
    return tools


def dispatch_native_tool_call(tool_call, registry, granted_permissions):
    tool_name = tool_call.function.name
    args_json = tool_call.function.arguments
    
    if tool_name not in registry:
        return {"error": f"unknown tool: {tool_name}"}
    
    tool_spec = registry[tool_name]
    required_permission = tool_spec["permission"]
    
    if required_permission not in granted_permissions:
        return {"error": f"permission denied: '{tool_name}' requires '{required_permission}' permission"}
    
    try:
        args_dict = json.loads(args_json)
    except json.JSONDecodeError as e:
        return {"error": f"invalid arguments JSON: {args_json}"}
    
    valid, error = validate_arguments(tool_spec["parameters"], args_dict)
    if not valid:
        return {"error": f"invalid arguments: {error}"}
    
    try:
        result = tool_spec["fn"](**args_dict)
        return result
    except Exception as e:
        return {"error": f"tool execution failed: {e}"}


def run_native_loop(client, task, registry, granted_permissions, max_steps=MAX_AGENT_STEPS):
    tools_desc = build_native_tools(registry)
    messages = [
        {"role": "user", "content": task},
    ]
    steps = []
    for step in range(max_steps):
        response = call_with_retry(client, model="main", messages=messages, tools=tools_desc, tool_choice="auto")
        
        if response.choices[0].finish_reason != "tool_calls":
            final_answer = response.choices[0].message.content
            return {"task": task, "steps": steps, "final_answer": final_answer, "steps_taken": step + 1}
        
        messages.append(response.choices[0].message)
        
        tool_calls = response.choices[0].message.tool_calls
        
        for tool_call in tool_calls:
            result = dispatch_native_tool_call(tool_call, registry, granted_permissions)
            steps.append({"tool": tool_call.function.name, "result": result})
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)})
        
    return {"task": task, "steps": steps, "final_answer": None, "steps_taken": max_steps}


def compare_traces(client, tasks, registry, granted_permissions):
    native_fewer_steps_count = 0
    native_multiple_tool_calls_count = 0

    for task in tasks:
        hand_rolled_result = run_agent_loop(client, task, registry)
        native_result = run_native_loop(client, task, registry, granted_permissions)

        print(f"Task: {task}")
        print(f"Hand-rolled steps taken: {hand_rolled_result['steps_taken']}")
        print(f"Native steps taken: {native_result['steps_taken']}")

        if native_result['steps_taken'] < hand_rolled_result['steps_taken']:
            native_fewer_steps_count += 1

        if any(len(tool_calls) > 1 for response in native_result['steps'] for tool_calls in response.values()):
            native_multiple_tool_calls_count += 1

    print("\nAggregate results:")
    print(f"Tasks that took fewer steps natively: {native_fewer_steps_count}")
    print(f"Native runs with at least one turn with multiple tool calls: {native_multiple_tool_calls_count}")


def main():
    global TICKETS_STATUS
    TICKETS_STATUS = load_ticket_statuses()
    client = get_client()

    compare_traces(client, AGENT_TASKS, TOOL_REGISTRY, GRANTED_FULL)


if __name__ == "__main__":
    main()
