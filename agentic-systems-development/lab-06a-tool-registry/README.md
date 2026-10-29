# Lab 6a: The Tool Registry, Formally

Builds directly on Lab 5a's agent loop and Week 6's lecture. Same
ticket-support domain, now with four tools (`check_ticket_status`,
`escalate_ticket`, `search_tickets`, `reassign_ticket`) described by
one `TOOL_REGISTRY` structure instead of a hand-written prompt string
and a separate dispatch dict. `aider` is available for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

`run_agent_loop`, `run_agent_batch`, and `agent_summary_report` are
already implemented and given -- your job is the registry-specific
pieces the loop depends on: generating its prompt text, validating and
dispatching its tool calls, filtering a larger registry down to what's
relevant, and extending the registry with two new tools of your own.

## Exercises

1. **`validate_arguments(schema, arguments)`** -- validate a dict of
   arguments against a JSON Schema like the ones in `TOOL_REGISTRY`
   (`{"type": "object", "properties": {...}, "required": [...]}`).
   Return `(True, None)` if every required field in `schema["required"]`
   is present in `arguments`, and every field that *is* present matches
   its declared type (`"integer"` -> `int`, `"string"` -> `str`,
   `"number"` -> `int` or `float`, `"boolean"` -> `bool`). Otherwise
   return `(False, "<a specific, human-readable reason>")`. Extra
   fields not mentioned in `properties` are fine -- don't reject them.
2. **`build_tools_desc(registry)`** -- generate the prompt text the
   model reads, from the registry, instead of hand-typing it. For each
   tool, produce a line like
   `check_ticket_status(ticket_id: integer) -- Look up a ticket's status and age.`
   (name, then each property name and its JSON Schema `type` in
   parentheses, then the description) and join them under a header
   telling the model it has these tools. After the tool list, still
   need the same JSON-decision-shape instructions Lab 5a's `TOOLS_DESC`
   ended with (`{"action": "call_tool", ...}` / `{"action": "final_answer", ...}`).
3. **`dispatch_tool_call(decision, registry)`** -- same never-raise
   contract as Lab 5a: unknown tool name returns
   `{"error": "unknown tool: <name>"}`. Known tool: validate
   `decision.arguments` against that tool's schema with
   `validate_arguments` first -- if invalid, return
   `{"error": "invalid arguments: <reason>"}` **without calling the
   tool**. Only if validation passes, call `spec["fn"](**decision.arguments)`
   and return its result; if that raises `TypeError` anyway, return
   `{"error": "dispatch failed: <message>"}`.
4. **`filter_relevant_tools(registry, task, max_tools=3)`** -- Week
   6's lecture named this problem ("picking a tool from a longer
   menu") without building it. Build a simple version: split `task`
   into lowercase words (split on anything that isn't a letter or
   digit), and for each tool in `registry`, score it by how many of
   those words also appear in its name or description (also
   lowercased and word-split). Return a new dict containing only the
   `max_tools` highest-scoring entries (ties broken however you like,
   but never return more than `max_tools`). A tool that scores 0 should
   never be included even if fewer than `max_tools` tools scored above
   0.
5. **`close_ticket(ticket_id)`** -- append `ticket_id` to
   `CLOSED_TICKETS` and return `{"closed": True, "ticket_id": ticket_id}`.
   Then **add a `"close_ticket"` entry to `TOOL_REGISTRY` yourself** --
   same shape as the existing entries (`fn`, `description`,
   `parameters` as real JSON Schema with `ticket_id` required).
6. **`get_ticket_history(ticket_id)`** -- return
   `TICKET_HISTORY.get(ticket_id, {"error": "no such ticket"})`
   (`TICKET_HISTORY` is already given). Then **add a
   `"get_ticket_history"` entry to `TOOL_REGISTRY` yourself**, same as
   Exercise 5.

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
Exercises 5-6 are graded on behavior, not exact schema wording: your
`close_ticket`/`get_ticket_history` registry entries are graded by
whether `validate_arguments` correctly accepts a valid call and
rejects one missing `ticket_id`, using the schema you wrote -- not by
matching a specific JSON Schema string.
