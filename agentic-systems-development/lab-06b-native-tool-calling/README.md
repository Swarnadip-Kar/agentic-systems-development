# Lab 6b: Native Tool Calling

Builds directly on Lab 6a's registry (given here as finished, working
code -- including a `"permission"` field per tool, same idea as Lab
5b) and Week 6's lecture. The registry that generated a hand-rolled
prompt and drove hand-rolled dispatch now also drives real
`tools=`/`tool_choice="auto"` native function calling -- the same
structure, pointed at a different interface. `aider` is available for
this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

**This gateway's model now genuinely supports native tool calling**
(fixed the same week this lab was written -- see
`aise-lab-infra/docs/RUNBOOK.md` if you're curious why it didn't
before). `run_agent_loop` -- Lab 6a's hand-rolled loop -- is given here
unchanged, so you have a working baseline to compare against.

## Exercises

1. **`build_native_tools(registry)`** -- convert `TOOL_REGISTRY` into
   the list `tools=` expects: one
   `{"type": "function", "function": {"name": ..., "description": ...,
   "parameters": ...}}` per tool. `parameters` is already real JSON
   Schema (Lab 6a) -- copy it straight in, no translation needed.
2. **`dispatch_native_tool_call(tool_call, registry, granted_permissions)`**
   -- `tool_call` is one entry from `message.tool_calls` (has
   `.id`, `.function.name`, `.function.arguments` -- the last one is a
   JSON **string**, not a dict, so parse it with `json.loads` first;
   if that fails, return `{"error": "invalid arguments JSON: <message>"}`
   without raising). Unknown tool name: `{"error": "unknown tool: <name>"}`.
   Known tool: check `registry[name]["permission"]` against
   `granted_permissions` **first** -- if not granted, return
   `{"error": "permission denied: '<name>' requires '<permission>' permission"}`
   without calling anything. Only then validate the parsed arguments
   with `validate_arguments` (given, from Lab 6a) -- invalid arguments
   return `{"error": "invalid arguments: <reason>"}`. Only if
   everything passes, call the tool and return its result. Never
   raise, for any of these reasons.
3. **`run_native_loop(client, task, registry, granted_permissions, max_steps=MAX_AGENT_STEPS)`**
   -- the native version of `run_agent_loop`. Each turn: call
   `client.chat.completions.create(model="main", messages=messages,
   tools=build_native_tools(registry), tool_choice="auto")`. If
   `response.choices[0].finish_reason != "tool_calls"`, that's the
   final answer -- return it. Otherwise, **the response may contain
   more than one tool call in `message.tool_calls` -- dispatch every
   one of them**, not just the first, appending one
   `{"role": "tool", "tool_call_id": tool_call.id, "content":
   json.dumps(result)}` message per call (matching each call by its
   `id`), plus one `{"tool": name, "result": result}` entry per call
   to the returned `"steps"` list. `"steps_taken"` counts model calls
   (turns), not individual tool dispatches -- a turn with 3 parallel
   tool calls still only costs 1 step. Append the assistant's own
   turn to `messages` before the tool results, same shape Lab 6a's
   loop used but with `"tool_calls"` instead of hand-parsed JSON
   content.
4. **`compare_traces(client, tasks, registry, granted_permissions)`**
   -- for each task in `tasks`, run it through both
   `run_agent_loop` (hand-rolled, given) and `run_native_loop`
   (Exercise 3), under the same `granted_permissions`. Print, per
   task, both approaches' `steps_taken`. Then print an aggregate: how
   many tasks took fewer steps natively, and how many native runs
   included at least one turn with more than one tool call (a
   capability the hand-rolled protocol doesn't have).

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
