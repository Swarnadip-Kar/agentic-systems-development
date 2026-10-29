# Lab 5b: Permission and Scope Control on Tools

Builds directly on Lab 5a's agent loop. Same ticket-support domain,
same two tools -- this session adds a permission layer between the
model's decision and the tool actually running. `aider` is available
for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

**Why this matters:** during Lab 5a's own live verification, the model
escalated a ticket on a task that only asked for a read-only status
check -- nobody told it to. The model deciding to call a tool is not
the same as that call being *allowed*. `TOOLS_DESC` in this scaffold
never mentions permissions at all -- the model has no idea what it can
or can't do. The harness enforces that, not the model.

## Exercises

1. **`dispatch_tool_call(decision, tools, tool_permissions, granted_permissions)`**
   -- same job as Lab 5a's version (unknown tool / bad arguments both
   return `{"error": ...}`, never raise), plus a new check: look up
   `tool_permissions[decision.tool]` (`"read"` or `"write"`) and, if
   that permission isn't in `granted_permissions`, return
   `{"error": "permission denied: '<tool>' requires '<permission>' permission"}`
   **without calling the tool at all**. Check permission before
   attempting the call.
2. **`run_agent_loop(client, task, tools, tool_permissions, granted_permissions, max_steps=MAX_AGENT_STEPS)`**
   -- same loop shape as Lab 5a, now threading `tool_permissions` and
   `granted_permissions` through to `dispatch_tool_call` at each tool
   call. A permission-denied result is recorded as a step exactly like
   any other tool result (same `{"tool": <name>, "result": <dict>}`
   shape) and fed back to the model as the next turn -- the model sees
   it was denied and has to decide what to do next, same as any other
   tool outcome.
3. **`permission_denial_report(results)`** -- print a summary over a
   list of `run_agent_loop`-shaped result dicts: total permission-denied
   steps, and which tool(s) they were for (check each result's
   `"steps"` for a `"result"` dict containing an `"error"` starting
   with `"permission denied"`).
4. **`compare_permission_scopes(client, tasks, tools, tool_permissions)`**
   -- run `run_agent_batch` over `tasks` twice: once with
   `GRANTED_READ_ONLY`, once with `GRANTED_FULL` (both already
   defined). Print a comparison: how many `escalate_ticket` attempts
   were denied under read-only permission versus how many actually
   succeeded under full permission. This is the payoff -- same tasks,
   same model tendencies, different real-world outcome depending on
   what the harness actually allows.

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
