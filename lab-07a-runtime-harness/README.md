# Lab 7a: The Runtime Harness

Builds directly on Lab 6b's native tool-calling loop and Week 7's
lecture. Lab 6b's registry (with permissions), `build_native_tools`,
`dispatch_native_tool_call`, and `validate_arguments` are all given
here as finished code. `aider` is available for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

## The problem this lab fixes

Every loop you've written since Lab 5a looks like Lab 6b's
`run_native_loop`: the step bound (`for step in range(max_steps)`), the
model call, the tool dispatch, and the message bookkeeping all live in
one function. Want a wall-clock timeout? Edit the loop. Want to log
every step? Edit the loop. Want a broken tool to fail gracefully
instead of crashing the batch? Edit the loop. None of those are about
*deciding what to do next*, yet all of them mean touching the same
function.

This lab separates them: a pure step function that only decides, and
a `RuntimeHarness` that owns everything operational.

## Exercises

1. **`agent_step(state, client, registry, tools, granted_permissions)`**
   -- exactly one perceive-think-act-observe cycle, and nothing else.
   `state` is `{"messages": [...]}`. Call
   `client.chat.completions.create(model="main", messages=state["messages"],
   tools=tools, tool_choice="auto")`. If
   `response.choices[0].finish_reason != "tool_calls"`, return
   `(state, True, message.content)` -- the final answer. Otherwise:
   append the assistant turn to a **new** messages list (`content` plus
   `"tool_calls": [tc.model_dump() for tc in message.tool_calls]`),
   dispatch **every** tool call in `message.tool_calls` via
   `dispatch_native_tool_call`, append one
   `{"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}`
   per call, and return `({"messages": new_messages}, False, step_output)`
   where `step_output` is a list of `{"tool": name, "result": result}`
   per call. No `max_steps`, no timing, no `try/except` anywhere in
   here -- if a tool raises, let it propagate. That is deliberate.
2. **`RuntimeHarness.run(agent_step_fn, state)`** -- the harness. The
   constructor and `_log(entry)` (appends one JSON line to
   `self.trace_path`) are given. `agent_step_fn` takes just `state` and
   returns `(new_state, done, output)` -- the caller wraps Exercise 1 in
   a lambda to bind the other arguments. Implement, in this order, for
   `step` in `1..max_steps`:
   - Compute `elapsed = time.monotonic() - start`. If
     `elapsed > self.timeout_seconds`, log
     `{"step": step, "elapsed_s": elapsed, "status": "timeout"}` and
     return `{"status": "timeout", "steps_taken": step - 1, "elapsed_s": elapsed}`.
     This check runs *between* steps -- it will **not** catch a step
     that hangs mid-call (that is Lab 7b's problem; here, know that
     it's a limitation, don't try to solve it).
   - Call `agent_step_fn(state)` inside a single `try/except Exception as e`.
     On exception: log `{"step": step, "elapsed_s": ..., "status": "error",
     "error": f"{type(e).__name__}: {e}"}` and return
     `{"status": "error", "steps_taken": step, "error": <same string>}`.
   - On success: log `{"step": step, "elapsed_s": ..., "status": "ok",
     "output": output}`. If `done`, return
     `{"status": "done", "steps_taken": step, "output": output}`.
   - After the loop: return `{"status": "exhausted", "steps_taken": self.max_steps}`
     (no trace entry for this case).
   Round `elapsed_s` to 2 decimals in trace entries.
3. **`read_trace(trace_path)`** -- read the JSONL file back into a list
   of dicts, one per non-blank line, in order.
4. **`trace_summary(entries)`** -- return
   `{"total": <len>, "by_status": {<status>: <count>, ...},
   "avg_elapsed_s": <mean of "elapsed_s" over all entries, 0.0 if empty>,
   "last_status": <entries[-1]["status"], or None if empty>}`.
5. **`run_scenarios(client, registry, granted_permissions, trace_dir=".")`**
   -- for each scenario in `SCENARIOS` (given): pick the registry
   (`registry_with_broken_tool(registry, break_tool)` if `break_tool` is
   set, else `registry` as-is), build `tools` with `build_native_tools`,
   create a `RuntimeHarness(max_steps=scenario["max_steps"],
   trace_path=f"{trace_dir}/harness_trace_{name}.jsonl")`, **truncate
   that trace file first** (`open(path, "w").close()`), run it with
   `state = {"messages": [{"role": "user", "content": task}]}`, then
   print one line `name: status=<...> steps_taken=<...>` followed by
   the `trace_summary` of that scenario's trace. Return a list of
   `{"name": name, "result": result, "summary": summary}` in scenario
   order.

Run `python3 scaffold.py` to check your progress. Expected shape of a
correct run: `normal` finishes with `status=done`; `broken_tool` ends
with `status=error` and an `error` mentioning the escalation service;
`exhausted` (a 1-step budget on a multi-tool task) ends
`status=exhausted`. Exact step counts and wording vary run to run --
that's the model, not your code.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
The trace your harness writes (`harness_trace_*.jsonl`) is **yours** --
readable, in your repo, recording your loop's decisions. It is not the
same thing as the gateway trace the Grading line above refers to.
