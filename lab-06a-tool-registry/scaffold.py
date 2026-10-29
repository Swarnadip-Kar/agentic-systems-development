"""Lab 6a: the tool registry, formally, aider-assisted -- builds on
Lab 5a's agent loop and ticket-support domain. One structure per tool,
with real JSON Schema parameters, drives the prompt text AND dispatch
AND (Lab 6b, next) native tool calling."""
import json
import os
import re
import time
from pathlib import Path
from typing import Literal, Optional
import logging

from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, ValidationError, model_validator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Demo results, shaped exactly like run_agent_loop's return value --
# guarantees the budget-exhausted branch is exercised regardless of
# whether a given live run happens to blow its step budget. Same
# idiom as every prior lab's synthetic demo fixture.
AGENT_DEMO_RESULTS = [
    {
        "task": "Escalate ticket 501 if unresolved and older than 3 days.",
        "steps": [
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}},
            {"tool": "escalate_ticket", "result": {"escalated": True, "ticket_id": 501}},
        ],
        "final_answer": "Ticket 501 has been escalated.",
        "steps_taken": 3,
    },
    {
        "task": "Check ticket 502 and decide what to do.",
        "steps": [
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 10}},
        ] * 12,
        "final_answer": None,
        "steps_taken": MAX_AGENT_STEPS,
    },
]

# A larger, mixed-domain registry for Exercise 4 (tool selection at
# scale) -- the ticket tools plus decoys from unrelated domains. Not
# used by the live agent loop; a standalone fixture for
# filter_relevant_tools.
DECOY_TOOLS = {
    "get_weather_forecast": {
        "fn": lambda city: {"forecast": "sunny"},
        "description": "Get the weather forecast for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    "convert_currency": {
        "fn": lambda amount, to_currency: {"converted": amount},
        "description": "Convert an amount from one currency to another.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "to_currency": {"type": "string"},
            },
            "required": ["amount", "to_currency"],
        },
    },
    "send_email_notification": {
        "fn": lambda recipient, subject: {"sent": True},
        "description": "Send an email notification to a recipient.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "subject": {"type": "string"},
            },
            "required": ["recipient", "subject"],
        },
    },
    "translate_text": {
        "fn": lambda text, target_language: {"translated": text},
        "description": "Translate text into a target language.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target_language": {"type": "string"},
            },
            "required": ["text", "target_language"],
        },
    },
    "schedule_meeting": {
        "fn": lambda attendee, time: {"scheduled": True},
        "description": "Schedule a meeting with an attendee at a given time.",
        "parameters": {
            "type": "object",
            "properties": {
                "attendee": {"type": "string"},
                "time": {"type": "string"},
            },
            "required": ["attendee", "time"],
        },
    },
    "generate_invoice_pdf": {
        "fn": lambda customer: {"pdf": "invoice.pdf"},
        "description": "Generate an invoice PDF for a customer.",
        "parameters": {
            "type": "object",
            "properties": {"customer": {"type": "string"}},
            "required": ["customer"],
        },
    },
}


def load_ticket_statuses():
    data = json.loads(Path(__file__).with_name("tickets_status.json").read_text())
    return {row["id"]: {"status": row["status"], "age_days": row["age_days"]} for row in data}


def get_client():
    return OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )


def call_with_retry(client, messages):
    for attempt in range(4):
        try:
            return client.chat.completions.create(model="main", messages=messages)
        except (RateLimitError, APIError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def _strip_code_fence(text):
    return re.sub(r"^```json\s*|```\s*$", "", text.strip(), flags=re.MULTILINE).strip()


class AgentDecision(BaseModel):
    action: Literal["call_tool", "final_answer"]
    tool: Optional[str] = None
    arguments: Optional[dict] = None
    answer: Optional[str] = None

    @model_validator(mode="after")
    def check_required_fields(self):
        if self.action == "call_tool" and (self.tool is None or self.arguments is None):
            raise ValueError("call_tool requires both tool and arguments")
        if self.action == "final_answer" and self.answer is None:
            raise ValueError("final_answer requires answer")
        return self


def parse_agent_decision(raw_response_text):
    text = _strip_code_fence(raw_response_text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"response was not valid JSON: {e}"
    try:
        return AgentDecision(**data), None
    except ValidationError as e:
        return None, f"response failed schema validation: {e}"


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


# One entry per tool: the real function, its description, and its
# parameter shape as real JSON Schema -- everything needed to
# generate the prompt text, validate a call, and dispatch it, all
# from one source of truth.
TOOL_REGISTRY = {
    "check_ticket_status": {
        "fn": check_ticket_status,
        "description": "Look up a ticket's status and age.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
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
    },
    "search_tickets": {
        "fn": search_tickets,
        "description": "List ticket ids matching a status.",
        "parameters": {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
        },
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
    },
    "close_ticket": {
        "fn": close_ticket,
        "description": "Close a ticket.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
    },
    "get_ticket_history": {
        "fn": get_ticket_history,
        "description": "Get the history of a ticket.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
    },
}


def validate_arguments(schema, arguments):
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required_fields:
        if field not in arguments:
            return False, f"Missing required field: {field}"

    for field, value in arguments.items():
        if field in properties:
            expected_type = properties[field]["type"]
            if expected_type == "integer" and not isinstance(value, int):
                return False, f"Field {field} must be an integer"
            elif expected_type == "string" and not isinstance(value, str):
                return False, f"Field {field} must be a string"
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False, f"Field {field} must be a number"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False, f"Field {field} must be a boolean"

    return True, None


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
    if decision.tool not in registry:
        return {"error": f"unknown tool: {decision.tool}"}
    
    tool_info = registry[decision.tool]
    schema = tool_info["parameters"]
    valid, error = validate_arguments(schema, decision.arguments)
    if not valid:
        return {"error": f"invalid arguments: {error}"}
    
    try:
        result = tool_info["fn"](**decision.arguments)
        logging.info(f"Tool call: {decision.tool} with arguments {decision.arguments} resulted in {result}")
        return result
    except TypeError as e:
        logging.error(f"Dispatch failed: {e}")
        return {"error": f"dispatch failed: {e}"}


def filter_relevant_tools(registry, task, max_tools=3):
    task_words = set(word.lower() for word in re.findall(r'\w+', task))
    relevant_tools = {}

    for tool_name, tool_info in registry.items():
        score = sum(1 for word in task_words if word in tool_name.lower() or word in tool_info["description"].lower())
        if score > 0:
            relevant_tools[tool_name] = score
    
    sorted_tools = sorted(relevant_tools.items(), key=lambda x: x[1], reverse=True)
    return {tool_name: tool_info for tool_name, _ in sorted_tools[:max_tools]}


def run_agent_loop(client, task, registry, max_steps=MAX_AGENT_STEPS):
    logging.info(f"User prompt received: {task}")
    tools_desc = build_tools_desc(registry)
    messages = [
        {"role": "system", "content": tools_desc},
        {"role": "user", "content": task},
    ]
    steps = []
    for step in range(max_steps):
        response = call_with_retry(client, messages)
        raw = response.choices[0].message.content
        decision, error = parse_agent_decision(raw)
        if error:
            messages.append({"role": "user", "content": f"Error: {error}. Respond with valid JSON."})
            logging.error(f"Error in response: {error}")
            continue

        messages.append({"role": "assistant", "content": raw})
        logging.info(f"Model responded with action: {raw}")

        if decision.action == "final_answer":
            logging.info(f"Final answer: {decision.answer}")
            return {
                "task": task,
                "steps": steps,
                "final_answer": decision.answer,
                "steps_taken": step + 1,
            }

        result = dispatch_tool_call(decision, registry)
        steps.append({"tool": decision.tool, "result": result})
        messages.append({"role": "user", "content": f"Tool result: {json.dumps(result)}"})

    logging.info(f"Max steps reached without final answer.")
    return {"task": task, "steps": steps, "final_answer": None, "steps_taken": max_steps}


def run_agent_batch(client, tasks, registry, max_steps=MAX_AGENT_STEPS):
    return [run_agent_loop(client, task, registry, max_steps) for task in tasks]


def agent_summary_report(results):
    finished = sum(1 for r in results if r["final_answer"] is not None)
    exhausted = len(results) - finished
    with_escalation = sum(
        1 for r in results if any(s["tool"] == "escalate_ticket" for s in r["steps"])
    )
    avg_steps = sum(r["steps_taken"] for r in results) / len(results)
    print(f"finished: {finished}/{len(results)}, exhausted: {exhausted}/{len(results)}, "
          f"included escalation: {with_escalation}/{len(results)}, "
          f"avg steps: {avg_steps:.2f}")


def main():
    global TICKETS_STATUS
    TICKETS_STATUS = load_ticket_statuses()
    client = get_client()

    results = run_agent_batch(client, AGENT_TASKS, TOOL_REGISTRY)
    agent_summary_report(results)

    print("\n--- Report over the demo fixture (see README) ---")
    agent_summary_report(AGENT_DEMO_RESULTS)

    print("\n--- filter_relevant_tools demo ---")
    full_registry = {**TOOL_REGISTRY, **DECOY_TOOLS}
    task = "Check the status of my support ticket and escalate it if needed."
    relevant = filter_relevant_tools(full_registry, task, max_tools=3)
    print(f"task: {task!r}")
    print(f"selected tools: {list(relevant.keys())}")


if __name__ == "__main__":
    main()
