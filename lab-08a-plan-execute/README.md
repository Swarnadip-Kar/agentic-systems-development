# Lab 8a: Plan, Execute, Replan

Builds directly on Week 8's lecture. Week 7's `RuntimeHarness`, the ticket
tools and their registry, `dispatch`, and the lecture's `react_step` are all
given as finished code. `aider` is available for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` and `temperature=0` to
`client.chat.completions.create()`.

Your gateway key allows 30 model calls a minute. The given `CountingClient`
wraps a client, counts its calls, and paces them to stay under that limit,
so a run never stalls on a rejected call. Use it wherever this README says
to.

## A map of the code

`call-flow.pdf` in this repo draws the whole call chain: who calls whom, what
the harness loop does each round, the order of calls inside one planning
round, and how `state` grows across rounds in a real run. Keep it open while
you work.

## The problem this lab solves

The lecture's running task was: *find all unresolved tickets and escalate
every one that has never been escalated before.* Asked to plan it in one go,
the model wrote ticket ids it could not know yet, as placeholders like
`"{{search_tickets_result[0]}}"`, and the plan failed the moment it ran. The
fix was to plan a little, execute, show the planner what happened, and plan
again. This lab builds that loop, then measures it against ReAct.

The right answers are known: tickets 9, 23, and 42 are unresolved, and
ticket 9 was already escalated once. So the first task's answer is 23 and 42.

## Exercises

1. **`build_plan_schema(registry)`** -- the JSON schema the planner's answer
   must follow. An object with two required fields: `done`, a boolean, and
   `steps`, an array. Each step is an object with two required fields:
   `tool`, a string restricted by `"enum"` to the registry's tool names in
   registry order, and `arguments`, an object.

2. **`cut_before_unobserved_writes(plan, registry)`** -- the lecture's
   "observe before you write" rule, as a pure function. A tool is a *write*
   if its registry entry has `"permission": "write"`. If a write appears
   after any read in the plan, return the plan up to, but not including,
   that first such write. Otherwise return the plan unchanged. Steps whose
   tool is not in the registry are neither reads nor writes. Do not modify
   the list you were given.

3. **`execute_until_stuck(plan, registry, granted_permissions)`** -- run the
   plan's steps in order with the given `dispatch`, and return a list of
   observations.
   - For each step that ran, append the step with its result added:
     `{"tool": ..., "arguments": ..., "result": ...}`. This includes steps
     whose result is an error, such as an unknown tool or a denied
     permission.
   - If a result is an error whose text starts with `"invalid arguments"`,
     the arguments were wrong, usually a placeholder where an id should be.
     Do not record it as a result. Instead append
     `{"not_run": <tool name>, "why": "<the error text>. It was never
     executed. Plan this call again using real values from the results
     above."}` and stop: run no further steps.

4. **`plan_execute_step(state, client, registry, granted_permissions)`** --
   one round of planning and execution, written as a step function so it
   runs under the unchanged Week 7 harness. `state` is
   `{"task": str, "observations": list}`, as made by the given
   `plan_initial_state`.
   - Make exactly one model call, with `model="main"`, `temperature=0`,
     `messages=planner_messages(task, observations, registry)`, and
     `response_format={"type": "json_schema", "json_schema": {"name":
     "plan", "schema": build_plan_schema(registry)}}`.
   - Parse the reply's content as JSON.
   - If `done` is true, return `(state, True, "planner: done")`.
   - If there are no steps, the planner is confused. Return a new state
     with this one observation added, and `False`:
     `{"not_run": "anything", "why": "You said the task is not done but
     planned no steps."}`. The output is the list of new observations.
   - Otherwise apply `cut_before_unobserved_writes`, then
     `execute_until_stuck`. Return a new state with the new observations
     appended, `False`, and the list of new observations.
   - Never modify the state you were given.

5. **`compare_patterns(client, tasks=TASKS, runs=1, trace_dir=".")`** --
   measure the two patterns. For each task, then each pattern in the order
   `"react"`, `"plan-execute"`, then each run from 1 to `runs`:
   - Make a fresh `TicketWorld`, its registry, and
     `CountingClient(client)`.
   - Run a `RuntimeHarness` with `max_steps=MAX_ROUNDS` and
     `trace_path=f"{trace_dir}/trace_{task_id}_{pattern}_{run}.jsonl"`. Start
     the trace file empty. For `"react"`, the step function is the given
     `react_step` and the start state is `react_initial_state(task)`. For
     `"plan-execute"`, use yours and `plan_initial_state(task)`. Use
     `GRANTED_FULL` for both.
   - Record a row: `{"task": <task id>, "pattern": ..., "run": ...,
     "status": <the harness status>, "escalated": world.escalated_ids(),
     "calls": <the CountingClient's calls>, "correct": ...}`. A run is
     correct only if its status is `"done"` and `escalated` equals the
     task's `expected_escalations`, sorted.
   - Print one line per row, and return the list of rows in the order they
     ran.

Run `python3 scaffold.py` to compare the patterns on the three tasks. Read
the trace files for any run that was not correct: which turn escalated a
ticket, and had its history been read yet?

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
