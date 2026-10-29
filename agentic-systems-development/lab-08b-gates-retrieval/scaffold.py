"""Lab 8b: approval gates and retrieval -- aider-assisted. Builds directly
on Lab 8a (its planner is given here as finished code) and Week 8's
lecture. You put a human in front of the planner's writes, and give the
agent a runbook to read."""
import collections
import json
import os
import re
import threading
import time
from pathlib import Path

import openai

MAX_ROUNDS = 10
DEFAULT_TIMEOUT_SECONDS = 180
RATE_LIMIT_RPM = 28  # every gateway key allows 30 calls a minute

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


# --- Lab 8a's planner, given as finished code -------------------------------

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
        model="main", temperature=0,
        messages=planner_messages(state["task"], state["observations"], registry),
        response_format={"type": "json_schema",
                         "json_schema": {"name": "plan", "schema": build_plan_schema(registry)}},
    )
    return json.loads(response.choices[0].message.content)


def is_write(step, registry):
    return registry.get(step["tool"], {}).get("permission") == "write"


def gated_initial_state(task):
    return {"task": task, "observations": [], "denied": []}


# --- the runbook and retrieval helpers ------------------------------------------

def load_runbook():
    return json.loads(Path(__file__).with_name("runbook.json").read_text())


def load_questions():
    return json.loads(Path(__file__).with_name("questions.json").read_text())


RUNBOOK = load_runbook()

# Common English words, plus words that appear all over this runbook
# ("customer", "ticket", "agent") and so say nothing about which article fits.
STOPWORDS = set(
    "a an the is are was were be and or to of for in on at with what should i do does it its "
    "has have how can before after them they their my our we you that this when only say says "
    "who whom somebody me am us about customer customers ticket tickets agent agents".split()
)


def tokens(text):
    """Lowercase words and numbers in text, minus stopwords, as a set."""
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


NOT_COVERED = "The runbook does not cover this."

ANSWER_SYSTEM = ("Answer the support agent's question using only the runbook excerpts given. "
                 "If the excerpts do not answer it, say that the runbook does not cover it.")


def answer_messages(question, doc_ids):
    excerpts = "\n\n".join(f"[{d}] {RUNBOOK[d]}" for d in doc_ids)
    return [{"role": "system", "content": ANSWER_SYSTEM},
            {"role": "user", "content": f"Runbook excerpts:\n{excerpts}\n\nQuestion: {question}"}]


RETRIEVAL_AGENT_SYSTEM = ("You answer support agents' questions about policy. Your only tool "
                          "searches the runbook; you cannot act on tickets. Search before "
                          "answering, and answer only from what the runbook says.")


def retrieval_agent_state(question):
    return {"messages": [{"role": "system", "content": RETRIEVAL_AGENT_SYSTEM},
                         {"role": "user", "content": question}]}


# Exercise 5: fill this in. Keys are single lowercase words a person might
# use; values are lists of words the runbook uses instead.
SYNONYMS = {
    # refunds
    "money": ["refunds"],
    "refund": ["refunds"],
    "reimburse": ["refunds"],
    "reimbursement": ["refunds"],
    # security incidents
    "permission": ["unauthorized", "access"],
    "logged": ["access"],
    "login": ["access"],
    "hacked": ["unauthorized", "access", "security"],
    "breach": ["security", "incidents"],
    "password": ["credentials"],
    "leak": ["leaked"],
    "incident": ["incidents"],
    # reassignment
    "leave": ["unavailable"],
    "absent": ["unavailable"],
    "away": ["unavailable"],
    "sick": ["unavailable"],
    "vacation": ["unavailable"],
    "transfer": ["reassign"],
    # sla targets
    "wait": ["response"],
    "target": ["targets"],
    "deadline": ["targets", "resolution"],
    "sla": ["service", "level", "targets"],
    # priority levels
    "serious": ["priority", "urgent"],
    "severity": ["priority", "levels"],
    "critical": ["urgent"],
    "app": ["product"],
    "down": ["cannot", "product"],
    "outage": ["urgent", "cannot", "product"],
    # data requests
    "erase": ["deleted"],
    "delete": ["deleted"],
    "gdpr": ["personal", "data", "privacy"],
    "request": ["requests"],
}


# --- your work ---------------------------------------------------------------

def make_gated_step(client, registry, granted_permissions, approver):
    def gated_step(state):
        denied = list(state["denied"])
        plan = plan_decision(state, client, registry)
        if plan["done"]:
            return state, True, "planner: done"

        steps = cut_before_unobserved_writes(plan["steps"], registry)
        if not steps:
            new_observations = [{"not_run": "anything", "why": "You said the task is not done but planned no steps."}]
            return {**state, "observations": state["observations"] + new_observations}, False, new_observations

        write_steps = [step for step in steps if is_write(step, registry)]
        if not write_steps:
            observations = execute_until_stuck(steps, registry, granted_permissions)
            return {**state, "observations": state["observations"] + observations}, False, observations

        writes_key = json.dumps(write_steps, sort_keys=True)
        if writes_key in state["denied"]:
            new_observations = [{"not_run": "writes", "why": "These writes were already denied by a human reviewer. Do not propose them again."}]
            return {**state, "observations": state["observations"] + new_observations}, False, new_observations

        if approver(write_steps):
            observations = execute_until_stuck(steps, registry, granted_permissions)
            return {**state, "observations": state["observations"] + observations}, False, observations
        else:
            new_observations = [{"not_run": "writes", "why": "A human reviewer denied these writes. Do not propose them again."}]
            new_denied = state["denied"] + [writes_key]
            return {**state, "observations": state["observations"] + new_observations, "denied": new_denied}, False, new_observations

    return gated_step


def retrieve(query, k=2):
    query_tokens = tokens(query)
    scores = []
    for doc_id, text in RUNBOOK.items():
        article_tokens = tokens(text)
        score = len(query_tokens.intersection(article_tokens))
        if score > 0:
            scores.append((score, doc_id))
    scores.sort(key=lambda x: (-x[0], x[1]))
    return [doc_id for _, doc_id in scores[:k]]


def retrieve_then_answer(question, client, retriever=retrieve):
    doc_ids = retriever(question)
    if not doc_ids:
        return ([], NOT_COVERED)
    response = client.chat.completions.create(
        model="main", temperature=0, messages=answer_messages(question, doc_ids)
    )
    return (doc_ids, response.choices[0].message.content)


def build_runbook_registry(retriever=retrieve):
    return {
        "search_runbook": {
            "fn": lambda query: [{"id": d, "text": RUNBOOK[d]} for d in retriever(query)],
            "description": "Search the runbook for relevant excerpts based on the query.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                           "required": ["query"]},
            "permission": "read",
        }
    }


def answer_with_search_tool(question, client, retriever=retrieve, trace_path="trace_search.jsonl"):
    registry = build_runbook_registry(retriever)
    harness = RuntimeHarness(max_steps=6, trace_path=trace_path)
    open(harness.trace_path, "w").close()
    result = harness.run(lambda state: react_step(state, client, registry, {"read"}),
                         retrieval_agent_state(question))
    searches = []
    for entry in read_trace(trace_path):
        if entry.get("status") != "ok" or not isinstance(entry.get("output"), list):
            continue
        for item in entry["output"]:
            if isinstance(item, dict) and item.get("tool") == "search_runbook":
                res = item.get("result")
                ids = [r["id"] for r in res] if isinstance(res, list) else []
                searches.append((item["arguments"].get("query"), ids))
    answer = result["output"] if result["status"] == "done" else None
    return searches, answer


def expand_query(query, synonyms=SYNONYMS):
    expanded_words = []
    for word in re.findall(r"[a-z0-9]+", query.lower()):
        expanded_words.append(word)
        if word in synonyms:
            expanded_words.extend(synonyms[word])
    return " ".join(expanded_words)


def retrieve_expanded(query, k=2):
    return retrieve(expand_query(query), k)


def hit_rate(questions, retriever):
    hits = sum(1 for q in questions if q["expected"] in retriever(q["question"]))
    return hits, len(questions)


# --- run it ---------------------------------------------------------------------

def deny_all(writes):
    print("   reviewer sees:", json.dumps(writes), "-> DENIED")
    return False


def approve_all(writes):
    print("   reviewer sees:", json.dumps(writes), "-> approved")
    return True


GATE_TASK = ("Find all unresolved tickets and escalate every one that has never been "
             "escalated before. Give a one-line reason for each escalation.")


def main():
    client = get_client()
    questions = load_questions()

    print("== retrieval hit rate on questions.json (top 2)")
    hits, total = hit_rate(questions, retrieve)
    print(f"   plain keywords:  {hits}/{total}")
    hits, total = hit_rate(questions, retrieve_expanded)
    print(f"   with SYNONYMS:   {hits}/{total}")

    print("\n== retrieve, then answer")
    for q in ["When am I allowed to close a ticket?", "What is the office wifi password?"]:
        doc_ids, answer = retrieve_then_answer(q, CountingClient(client))
        print(f"   {q}\n     retrieved {doc_ids}: {answer.strip()[:200]}")

    print("\n== the agent searches for itself")
    for label, retriever in [("plain keywords", retrieve), ("with SYNONYMS", retrieve_expanded)]:
        searches, answer = answer_with_search_tool(
            "A customer wants their money back. Who handles that?", CountingClient(client),
            retriever=retriever, trace_path=f"trace_search_{retriever.__name__}.jsonl")
        print(f"   {label}:")
        for query, found in searches:
            print(f"     searched {json.dumps(query)} -> {found}")
        print(f"     answer: {str(answer).strip()[:200]}")

    print("\n== the approval gate")
    for approver in (deny_all, approve_all):
        world = TicketWorld()
        registry = build_registry(world)
        harness = RuntimeHarness(trace_path=f"trace_gate_{approver.__name__}.jsonl")
        open(harness.trace_path, "w").close()
        result = harness.run(make_gated_step(CountingClient(client), registry, GRANTED_FULL, approver),
                             gated_initial_state(GATE_TASK))
        print(f"   {approver.__name__}: status {result['status']}, escalated {world.escalated_ids()}")


if __name__ == "__main__":
    main()
