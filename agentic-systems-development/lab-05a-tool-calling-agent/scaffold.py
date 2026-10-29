"""Lab 5a: build a two-tool agent loop from scratch, aider-assisted --
same ticket-support domain as Weeks 3-4, extended with a status/age
lookup a single classification call could never answer on its own."""
import json
import os
import re
import time
from pathlib import Path
from typing import Literal, Optional
import logging
from pydantic import BaseModel, model_validator, ValidationError
from openai import OpenAI, RateLimitError, APIError

MAX_AGENT_STEPS = 4

TICKETS_STATUS = {}  # populated by load_ticket_statuses() in main()

# The tasks run_agent_batch executes. Covers: a plain lookup, an
# escalate-worthy ticket, two different no-escalate cases (resolved;
# too young), a task needing the same tool called twice (comparison),
# and an unknown ticket ID (tests dispatch_tool_call's error path).
AGENT_TASKS = [
    "Check the status of ticket 1.",
    "Check ticket 1. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Check ticket 2. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Check ticket 3. If it is unresolved and older than 3 days, escalate it with a short reason.",
    "Which ticket has been open longer: ticket 4 or ticket 6? Answer with the ticket ID and its age in days.",
    "Check ticket 42. If it is unresolved and older than 3 days, escalate it with a short reason.",
]

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

# Demo results, shaped exactly like run_agent_loop's return value (see
# README Exercise 4) -- covers escalated, cleanly-resolved-no-escalation,
# and budget-exhausted-without-an-answer. A live batch reliably produces
# the first two, but a well-prompted model rarely blows its step
# budget, so that branch needs a guaranteed trigger -- same idiom as
# every prior lab's synthetic demo fixture.
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
        "task": "Check ticket 502.",
        "steps": [
            {"tool": "check_ticket_status", "result": {"status": "resolved", "age_days": 1}},
        ],
        "final_answer": "Ticket 502 is resolved.",
        "steps_taken": 2,
    },
    {
        "task": "Check ticket 503 and decide what to do.",
        "steps": [
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 10}},
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 10}},
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 10}},
            {"tool": "check_ticket_status", "result": {"status": "unresolved", "age_days": 10}},
        ],
        "final_answer": None,
        "steps_taken": MAX_AGENT_STEPS,
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
    # max_retries=0: same reasoning as Lab 4b -- the SDK's own internal
    # retries would silently swallow the failures call_with_retry needs
    # to actually see.
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


def check_ticket_status(ticket_id):
    logger.debug(f"check_ticket_status({ticket_id})")  #LOG
    return TICKETS_STATUS.get(ticket_id, {"error": "no such ticket"})  #LOG


def _strip_code_fence(text):
    # Models sometimes wrap JSON in ```json ... ``` even when told not
    # to -- same real-world wrinkle Week 4's cold open was built on.
    return re.sub(r"^```json\s*|```\s*$", "", text.strip(), flags=re.MULTILINE).strip()


class AgentDecision(BaseModel):
    action: Literal["call_tool", "final_answer"]
    tool: Optional[str] = None
    arguments: Optional[dict] = None
    answer: Optional[str] = None

    @model_validator(mode="after")
    def check_action_fields(cls, values):
        if values.action == "call_tool":
            if not all([values.tool, values.arguments]):
                raise ValueError("When action is 'call_tool', both tool and arguments must be set.")
        elif values.action == "final_answer":
            if not values.answer:
                raise ValueError("When action is 'final_answer', answer must be set.")
        return values


def parse_agent_decision(raw_response_text):
    try:
        stripped_text = _strip_code_fence(raw_response_text)
        data = json.loads(stripped_text)
        decision = AgentDecision(**data)
        logger.debug(f"parse_agent_decision({raw_response_text}) -> {json.dumps(decision.dict(), indent=4)}")  #LOG
        return decision, None
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"parse_agent_decision({raw_response_text}) -> Error: {e}")  #LOG
        return None, str(e)


def dispatch_tool_call(decision, tools):
    try:
        tool = tools.get(decision.tool)
        if tool is None:
            logger.error(f"dispatch_tool_call({decision}) -> Unknown tool: {decision.tool}")  #LOG
            return {"error": f"Unknown tool: {decision.tool}"}
        result = tool(**decision.arguments)
        logger.debug(f"dispatch_tool_call({decision}) -> Result: {json.dumps(result, indent=4)}")  #LOG
        return result
    except TypeError as e:
        logger.error(f"dispatch_tool_call({decision}) -> Error: {e}")  #LOG
        return {"error": str(e)}


def run_agent_loop(client, task, tools, max_steps=MAX_AGENT_STEPS):
    conversation = [
        {"role": "system", "content": TOOLS_DESC},
        {"role": "user", "content": task},
    ]
    steps = []
    steps_taken = 0
    final_answer = None

    while steps_taken < max_steps:
        logger.debug(f"run_agent_loop(conversation={json.dumps(conversation, indent=4)}, task={task}, tools={tools}, max_steps={max_steps})")  #LOG
        response = call_with_retry(client, conversation)
        raw_response_text = response.choices[0].message.content
        decision, error_message = parse_agent_decision(raw_response_text)

        if error_message:
            conversation.append({"role": "assistant", "content": raw_response_text})
            conversation.append({"role": "user", "content": f"Error: {error_message}"})
            steps_taken += 1
            continue

        if decision.action == "final_answer":
            final_answer = decision.answer
            logger.debug(f"run_agent_loop(final_answer={final_answer})")  #LOG
            break

        if decision.action == "call_tool":
            result = dispatch_tool_call(decision, tools)
            steps.append({"tool": decision.tool, "result": result})
            conversation.append({"role": "assistant", "content": raw_response_text})
            conversation.append({"role": "user", "content": json.dumps(result)})
            steps_taken += 1

    logger.debug(f"run_agent_loop(steps={json.dumps(steps, indent=4)}, final_answer={final_answer}, steps_taken={steps_taken})")  #LOG
    return {
        "task": task,
        "steps": steps,
        "final_answer": final_answer,
        "steps_taken": steps_taken,
    }


def escalate_ticket(ticket_id, reason):
    logger.debug(f"escalate_ticket({ticket_id}, {reason})")  #LOG
    ESCALATIONS.append({"ticket_id": ticket_id, "reason": reason})
    return {"escalated": True, "ticket_id": ticket_id}


ESCALATIONS = []
TOOL_REGISTRY = {
    "check_ticket_status": check_ticket_status,
    "escalate_ticket": escalate_ticket,
}


def run_agent_batch(client, tasks, tools, max_steps=MAX_AGENT_STEPS):
    results = []
    for task in tasks:
        result = run_agent_loop(client, task, tools, max_steps=max_steps)
        results.append(result)
    logger.debug(f"run_agent_batch(results={json.dumps(results, indent=4)})")  #LOG
    return results


def agent_summary_report(results):
    finished_with_answer = sum(1 for result in results if result["final_answer"] is not None)
    exhausted_max_steps = len(results) - finished_with_answer
    escalated_count = sum(1 for result in results for step in result["steps"] if step["tool"] == "escalate_ticket")
    average_steps_taken = sum(result["steps_taken"] for result in results) / len(results) if results else 0

    logger.info(f"Finished with final answer: {finished_with_answer}")  #LOG
    logger.info(f"Exhausted max steps without answer: {exhausted_max_steps}")  #LOG
    logger.info(f"Included escalate_ticket call: {escalated_count}")  #LOG
    logger.info(f"Average steps taken: {average_steps_taken:.2f}")  #LOG


def main():
    global TICKETS_STATUS
    TICKETS_STATUS = load_ticket_statuses()
    client = get_client()

    results = run_agent_batch(client, AGENT_TASKS, TOOL_REGISTRY)
    agent_summary_report(results)

    print("\n--- Report over the demo fixture (see README) ---")
    agent_summary_report(AGENT_DEMO_RESULTS)


if __name__ == "__main__":
    main()
