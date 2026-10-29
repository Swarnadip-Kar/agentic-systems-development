"""Lab 5b: permission/scope control on tools, aider-assisted -- builds
directly on Lab 5a's agent loop, same ticket-support domain. Every tool
now carries a read/write permission, and the harness -- not the model --
decides whether a call is actually allowed to run."""
import json
import os
import re
import time
from pathlib import Path
from typing import Literal, Optional
import logging
from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, ValidationError, model_validator

MAX_AGENT_STEPS = 4

TICKETS_STATUS = {}  # populated by load_ticket_statuses() in main()

AGENT_TASKS = [
    "Check the status of ticket 1.",
    "Check ticket 1. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Check ticket 2. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Check ticket 3. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Which ticket has been open longer: ticket 4 or ticket 6? Answer with the ticket ID and its age in days.",
    "Check ticket 42. If it is unresolved and older than 3 days, escalate it with a short reason.",
]

# Unchanged from Lab 5a -- never mentions permissions.
TOOLS_DESC = (
    "You have exactly two tools:\n"
    "check_ticket_status(ticket_id: int) -> {status: str, age_days: int}\n"
    "escalate_ticket(ticket_id: int, reason: str) -> {escalated: bool}\n\n"
    "At each turn respond with ONLY a JSON object, no other text, in one "
    "of these shapes:\n"
    '{"action": "call_tool", "tool": "check_ticket_status", '
    '"arguments": {"ticket_id": <int>}}\n'
    '{"action": "call_tool", "tool": "escalate_ticket", '
    '"arguments": {"ticket_id": <int>, "reason": "<str>"}}\n'
    '{"action": "final_answer", "answer": "<your answer>"}'
)

# Every tool's required permission. check_ticket_status only reads;
# escalate_ticket writes a real side effect.
TOOL_PERMISSIONS = {
    "check_ticket_status": "read",
    "escalate_ticket": "write",
}
GRANTED_READ_ONLY = {"read"}
GRANTED_FULL = {"read", "write"}

# Demo results, shaped exactly like run_agent_loop's return value --
# guarantees at least one permission-denied step is present regardless
# of whether the live read-only batch happens to attempt escalate_ticket
# this run. Same idiom as every prior lab's synthetic demo fixture.
AGENT_DEMO_RESULTS_READ_ONLY = [
    {
        "task": "Escalate ticket 501 if unresolved and older than 3 days.",
        "steps": [
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 6}},
            {"tool": "escalate_ticket",
             "result": {"error": "permission denied: 'escalate_ticket' requires 'write' permission"}},
        ],
        "final_answer": "Ticket 501 is unresolved and old, but I am not permitted to escalate it.",
        "steps_taken": 3,
    },
    {
        "task": "Check ticket 502.",
        "steps": [
            {"tool": "check_ticket_status", "result": {"status": "resolved", "age_days": 1}},
        ],
        "final_answer": "Ticket 502 is resolved.",
        "steps_taken": 2,
    },
]


def load_ticket_statuses():
    data = json.loads(Path(__file__).with_name("tickets_status.json").read_text())
    return {row["id"]: {"status": row["status"], "age_days": row["age_days"]} for row in data}


logger = logging.getLogger('agent_logger')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_client():
    return OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )


def call_with_retry(client, messages):
    for attempt in range(9):
        try:
            return client.chat.completions.create(model="main", messages=messages)
        except (RateLimitError, APIError):
            if attempt == 8:
                raise
            time.sleep(2 ** attempt)


def check_ticket_status(ticket_id):
    logger.debug(f"check_ticket_status({ticket_id})")
    return TICKETS_STATUS.get(ticket_id, {"error": "no such ticket"})


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
        logger.error(f"parse_agent_decision({raw_response_text}) -> Error: response was not valid JSON: {e}")
        return None, f"response was not valid JSON: {e}"
    try:
        decision = AgentDecision(**data)
        logger.debug(f"parse_agent_decision({raw_response_text}) -> {json.dumps(decision.dict(), indent=4)}")
        return decision, None
    except ValidationError as e:
        logger.error(f"parse_agent_decision({raw_response_text}) -> Error: response failed schema validation: {e}")
        return None, f"response failed schema validation: {e}"


def escalate_ticket(ticket_id, reason):
    logger.debug(f"escalate_ticket({ticket_id}, {reason})")
    ESCALATIONS.append({"ticket_id": ticket_id, "reason": reason})
    return {"escalated": True, "ticket_id": ticket_id}


ESCALATIONS = []
TOOL_REGISTRY = {
    "check_ticket_status": check_ticket_status,
    "escalate_ticket": escalate_ticket,
}


def dispatch_tool_call(decision, tools, tool_permissions, granted_permissions):
    tool_name = decision.tool
    if tool_name not in tools:
        logger.error(f"dispatch_tool_call({decision}) -> Unknown tool: {decision.tool}")
        return {"error": f"unknown tool: '{tool_name}'"}
    
    required_permission = tool_permissions.get(tool_name)
    if required_permission not in granted_permissions:
        logger.error(f"dispatch_tool_call({decision}) -> Permission denied: '{tool_name}' requires '{required_permission}' permission")
        return {"error": f"permission denied: '{tool_name}' requires '{required_permission}' permission"}
    
    try:
        result = tools[tool_name](**decision.arguments)
        logger.debug(f"dispatch_tool_call({decision}) -> Result: {json.dumps(result, indent=4)}")
        return result
    except TypeError as e:
        logger.error(f"dispatch_tool_call({decision}) -> Error: bad arguments for '{tool_name}': {e}")
        return {"error": f"bad arguments for '{tool_name}': {e}"}


def run_agent_loop(client, task, tools, tool_permissions, granted_permissions, max_steps=MAX_AGENT_STEPS):
    conversation = [
        {"role": "system", "content": TOOLS_DESC},
        {"role": "user", "content": task},
    ]
    steps = []
    steps_taken = 0

    while steps_taken < max_steps:
        logger.debug(f"run_agent_loop(conversation={json.dumps(conversation, indent=4)}, task={task}, tools={tools}, tool_permissions={tool_permissions}, granted_permissions={granted_permissions}, max_steps={max_steps})")
        response = call_with_retry(client, conversation)
        raw_response_text = response.choices[0].message.content
        decision, error_message = parse_agent_decision(raw_response_text)

        if error_message:
            conversation.append({"role": "assistant", "content": raw_response_text})
            conversation.append({"role": "user", "content": f"Error: {error_message}"})
            steps_taken += 1
            continue

        if decision.action == "final_answer":
            logger.debug(f"run_agent_loop(final_answer={decision.answer})")
            return {
                "task": task,
                "steps": steps,
                "final_answer": decision.answer,
                "steps_taken": steps_taken + 1,
            }

        if decision.action == "call_tool":
            result = dispatch_tool_call(decision, tools, tool_permissions, granted_permissions)
            steps.append({"tool": decision.tool, "result": result})
            conversation.append({"role": "assistant", "content": raw_response_text})
            conversation.append({"role": "user", "content": json.dumps(result)})
            steps_taken += 1

    logger.debug(f"run_agent_loop(steps={json.dumps(steps, indent=4)}, final_answer=None, steps_taken={steps_taken})")
    return {
        "task": task,
        "steps": steps,
        "final_answer": None,
        "steps_taken": steps_taken,
    }


def run_agent_batch(client, tasks, tools, tool_permissions, granted_permissions, max_steps=MAX_AGENT_STEPS):
    results = []
    for task in tasks:
        result = run_agent_loop(client, task, tools, tool_permissions, granted_permissions, max_steps=max_steps)
        results.append(result)
    logger.debug(f"run_agent_batch(results={json.dumps(results, indent=4)})")
    return results


def permission_denial_report(results):
    permission_denied_count = 0
    denied_tools = set()

    for result in results:
        for step in result["steps"]:
            if isinstance(step["result"], dict) and step["result"].get("error", "").startswith("permission denied"):
                permission_denied_count += 1
                denied_tools.add(step["tool"])

    logger.info(f"Total permission-denied steps: {permission_denied_count}")
    logger.info(f"Tools with permission denied: {', '.join(denied_tools)}")


def compare_permission_scopes(client, tasks, tools, tool_permissions):
    read_only_results = run_agent_batch(client, tasks, tools, tool_permissions, GRANTED_READ_ONLY)
    full_results = run_agent_batch(client, tasks, tools, tool_permissions, GRANTED_FULL)

    read_only_denials = sum(
        1 for result in read_only_results for step in result["steps"]
        if isinstance(step["result"], dict) and step["result"].get("error", "").startswith("permission denied")
    )

    full_successes = sum(
        1 for result in full_results for step in result["steps"]
        if step["tool"] == "escalate_ticket" and isinstance(step["result"], dict) and step["result"].get("escalated")
    )

    logger.info(f"Escalate ticket attempts denied under read-only permission: {read_only_denials}")
    logger.info(f"Escalate ticket attempts succeeded under full permission: {full_successes}")


def main():
    global TICKETS_STATUS
    TICKETS_STATUS = load_ticket_statuses()
    client = get_client()

    compare_permission_scopes(client, AGENT_TASKS, TOOL_REGISTRY, TOOL_PERMISSIONS)

    logger.info("\n--- Permission-denial report over the demo fixture (see README) ---")
    permission_denial_report(AGENT_DEMO_RESULTS_READ_ONLY)


if __name__ == "__main__":
    main()
