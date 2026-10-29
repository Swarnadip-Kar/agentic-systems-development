# Lab 7b: Bounding the Unboundable

Builds directly on Lab 7a's runtime harness and Week 7's lecture. Lab
7a's `agent_step`, `RuntimeHarness`, `read_trace`, `trace_summary`,
the registry, and the native dispatch are all given here as finished
code. `aider` is available for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

## The gap this lab closes

Lab 7a's `RuntimeHarness.run` checks the clock once per iteration,
*before* calling `agent_step_fn`. If the step itself hangs -- a tool
doing blocking I/O that never returns, a stuck subprocess, a model
call that never answers -- the loop is stuck on that one line and the
clock is never checked again. The harness's timeout is *cooperative*:
it only works if the thing being bounded hands control back. A hang
needs a *preemptive* bound. This lab builds the two fixes from the
lecture, adds a third that the lecture did not cover, and then
measures what each one lets the agent keep. The bound can sit in three
places -- around the model call, around the whole step, or around one
tool call -- and *where* it sits decides what survives a hang: nothing,
the deadline, or the answer.

One honest limit up front: Python can ask a blocking call to give up,
but it cannot force-kill a thread that is already running. Fixes 2 and
3 abandon a hung call; they do not stop it. Exercise 3 deals with the
consequence of that.

## Exercises

1. **`agent_step_with_timeout(state, client, registry, tools, granted_permissions, model_call_timeout=DEFAULT_MODEL_CALL_TIMEOUT)`**
   -- Fix 1. Identical to the given `agent_step` except the model call
   passes `timeout=model_call_timeout` to
   `client.chat.completions.create(...)`. That's the whole fix: the
   SDK enforces the deadline at the HTTP level and raises
   `openai.APITimeoutError` on its own, which the **unchanged** Lab 7a
   harness already turns into `{"status": "error", ...}`. Zero harness
   changes needed. It only covers the model call, though -- a hang
   inside a *tool* is untouched.
2. **`PreemptiveRuntimeHarness.run(agent_step_fn, state)`** -- Fix 2.
   Same constructor, `_log`, result shapes, and trace entries as Lab
   7a's harness (inherited). The difference is *where* the bound is:
   run each step in a worker thread and wait on it with a deadline.
   For `step` in `1..max_steps`:
   - `remaining = self.timeout_seconds - (time.monotonic() - start)`.
     If `remaining <= 0`: log `{"step", "elapsed_s", "status": "timeout"}`
     and return `{"status": "timeout", "steps_taken": step - 1}`.
   - `future = pool.submit(agent_step_fn, state)` then
     `state, done, output = future.result(timeout=remaining)`.
   - On `concurrent.futures.TimeoutError`: log
     `{"step", "elapsed_s", "status": "step_hung"}` and return
     `{"status": "timeout", "steps_taken": step - 1, "elapsed_s": ...,
     "note": "step exceeded the deadline and was abandoned, not killed"}`.
   - Any other exception, success, and exhaustion: exactly as Lab 7a.

   **Do not write `with ThreadPoolExecutor(...) as pool:`.** Leaving a
   `with` block calls `shutdown(wait=True)`, which blocks until every
   submitted task finishes -- including the hung one -- so your
   `return` will not actually complete until the hang does, and the
   timeout is silently defeated. Create the pool as a plain object and
   never shut it down from inside `run`. The oracle test for this
   exercise hands your harness a step that sleeps for 3 seconds under
   a 1-second timeout and checks that `run()` returns in about 1
   second; a `with`-based implementation fails it.
3. **`run_and_exit(harness, agent_step_fn, state)`** -- the consequence
   of "abandoned, not killed." A thread the harness gave up on is still
   running, and Python's normal interpreter shutdown waits for every
   `ThreadPoolExecutor` thread before it will exit -- so a script that
   just falls off the end sits there for the rest of the hang. This
   function runs `harness.run(agent_step_fn, state)`, prints
   `json.dumps(result)`, then ends the *process* immediately with
   `os._exit(0)`. But `os._exit` skips the interpreter's normal cleanup,
   which is also what flushes `stdout` -- so call `sys.stdout.flush()`
   right before it, or your printed result silently never appears. This
   function never returns. The oracle test runs it in a subprocess with
   a step that sleeps 30 seconds under a 1-second timeout and requires
   the process to exit within a few seconds *with the result on
   stdout* -- forgetting either half fails it, just at a different
   line.
4. **`dispatch_with_timeout(tool_call, registry, granted_permissions, tool_timeout=DEFAULT_TOOL_TIMEOUT)`**
   and **`agent_step_with_tool_timeout(state, client, registry, tools, granted_permissions, tool_timeout=DEFAULT_TOOL_TIMEOUT)`**
   -- Fix 3. Fix 2 saves the deadline but loses the run: the harness
   returns `timeout` and the user gets no answer. The bound was too
   coarse. Move it *inside* the step, around the one thing that hangs.
   `dispatch_with_timeout` submits
   `dispatch_native_tool_call(tool_call, registry, granted_permissions)`
   to a worker thread (same plain-pool rule as Exercise 2) and waits
   `future.result(timeout=tool_timeout)`. On success return the
   result unchanged -- permission, JSON, and schema errors still come
   back exactly as `dispatch_native_tool_call` produces them. On
   `concurrent.futures.TimeoutError` return
   `{"error": f"tool '{name}' timed out after {tool_timeout}s"}` --
   an ordinary tool result, the same shape as the dispatcher's other
   errors. `agent_step_with_tool_timeout` is the given `agent_step`
   with that one substitution, so the timeout error lands in a `tool`
   message and the *model* sees it on the next turn and can answer
   around it. The step returns normally; the unchanged Lab 7a harness
   moves on to the next step; the run finishes `done`.
5. **`compare_harnesses(client, registry, granted_permissions, scenarios=COMPARE_SCENARIOS, trace_dir=".")`**
   -- measure the difference. For each scenario: pick the registry
   (`registry_with_hanging_tool(registry, hang_tool, hang_seconds)` if
   `hang_tool` is set, else `registry` as-is), build `tools`, and run
   the same task through **three** configurations:
   - `cooperative`: `RuntimeHarness` driving the given `agent_step`;
   - `preemptive`: `PreemptiveRuntimeHarness` driving the given `agent_step`;
   - `tool_bounded`: `RuntimeHarness` driving `agent_step_with_tool_timeout`
     with the scenario's `tool_timeout_seconds`.

   Each harness is constructed with the scenario's `timeout_seconds`
   (default `max_steps`) and a trace file
   `f"{trace_dir}/harness_trace_{name}_{label}.jsonl"` (truncate it
   first). Time each `run()` with `time.monotonic()` around the call. A
   configuration "respected its deadline" if its wall-clock elapsed is
   `<= timeout_seconds + 1.0`. Print, per scenario and per
   configuration, `status`, `elapsed_s` (2 decimals), and
   `respected_deadline`; then an aggregate line per configuration:
   `respected deadline in N/M scenarios`. Return a list of
   `{"name", "cooperative": {"status", "elapsed_s", "respected_deadline"},
   "preemptive": {...same keys...}, "tool_bounded": {...same keys...}}`
   in scenario order.

Run `python3 scaffold.py` to check your progress. Expected shape: on
`normal` all three finish `done` and respect the deadline. On
`hanging_tool` (a 12-second hang under an 8-second harness timeout and
a 1-second tool timeout): `cooperative` ends `timeout` only *after*
sitting through the whole hang (`respected_deadline: False`, no
answer); `preemptive` returns `timeout` at 8 seconds (`True`, still no
answer); `tool_bounded` finishes `done` in roughly 4 to 7 seconds
(`True`) -- read its trace and the final message: the model was told
the tool timed out and answered with what it had. Often it retries the
tool once first, and each retry costs one tool timeout plus one model
call -- that retry is *visible in the trace*, which is the point: the
loop kept running, so the model's behaviour under failure became
observable instead of being buried inside a hang. Three bounds, three
outcomes. If the model happens not to call the tool at all on a given
run, nothing hangs -- that's live variance, rerun it. `main()` ends
with `os._exit(0)` for exactly the reason Exercise 3 describes.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
