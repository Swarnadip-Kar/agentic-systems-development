# Lab 9a: An Evaluation Harness for Your Own Agent

Builds on Week 9's lecture, "Tests for Agents". `aider` is available for
this session.

## The idea

You have an agent you can change: a prompt, a pattern, a model. When you
change it, is it better or worse? Trying it once on one task cannot tell
you. Software engineering's answer is tests whose answers are written down
**before** you trust the code, run on every change. An evaluation harness
is that, for an agent: test cases with known answers, checks, and a way to
run them all and compare two versions.

In this lab you build one around **your own Lab 8a planner**, and use it to
check the lecture's first prediction:

> ReAct fails the cases where a write depends on a read; your planner passes
> them. Where the path is known, both pass, and the planner costs more
> calls.

## What is given

Your Lab 8a planner (`plan_execute_step` and its pieces), the lecture's
`react_step`, Week 7's `RuntimeHarness`, the ticket world, `dispatch`, and a
`CountingClient` that counts model calls and paces them under the gateway's
30 calls a minute. `PATTERNS` maps each version's name to its step function
and its starting state. `test_set.json` holds eight test cases; six are
complete and two are missing their answers.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace.
`call-flow.pdf` in this repo maps who calls whom. Keep it open.

## Exercises

1. **Write the answers first.**
   - In `test_set.json`, the cases `younger-than-six-days` and
     `only-if-unresolved` have `"expected_escalations": null`. Work out each
     right answer from `tickets.json` by reading the data yourself, not by
     running an agent, and write it in as a list of ticket ids.
   - **`load_test_set(path="test_set.json")`** -- read the file and return
     the list of cases. Refuse a test set that is not ready: raise
     `ValueError` with a message containing the case's `id` if any case has
     `expected_escalations` that is not a list of integers (for example
     `null`), or a missing `id`, `task`, or `history_before_escalate`, or
     if two cases share an `id`. Return each case with its
     `expected_escalations` sorted.

2. **`check_outcome(case, world, result)`** -- return `(ok, detail)`.
   - If `result["status"]` is not `"done"`: `(False, "run ended with status <status>")`.
   - Otherwise compare `world.escalated_ids()` with the case's
     `expected_escalations`. Both are sorted lists, so escalating a ticket
     twice is wrong. If they differ:
     `(False, "escalated <got>, expected <expected>")`, using Python's list
     formatting, for example `escalated [9, 42, 42], expected [23, 42]`.
   - Otherwise `(True, "ok")`.

3. **`check_process(case, trace)`** -- return `(ok, detail)`. `trace` is the
   list from `read_trace`.
   - If the case's `history_before_escalate` is false: `(True, "not required")`.
   - Otherwise walk the trace in order. Only entries whose `output` is a
     list contain tool calls; skip entries without a `"tool"` key.
   - A history counts as read at the first step where a
     `get_ticket_history` call for that `ticket_id` returned a result with
     no `"error"`.
   - For every `escalate_ticket` call whose result has `"escalated": true`,
     its ticket's history must have been read at an **earlier** step. The
     same step does not count: the escalation was then decided before the
     history came back. On the first violation return
     `(False, "escalated ticket <id> in step <step> before its history had been read")`.
   - Otherwise `(True, "ok")`.

4. **`run_test_set(client, cases, patterns=("react", "plan-execute"), runs=1, trace_dir=".")`**
   -- for each case, then each pattern in the order given, then each run
   from 1 to `runs`:
   - make a fresh `TicketWorld`, its registry, and `CountingClient(client)`;
   - run a `RuntimeHarness` with `max_steps=MAX_ROUNDS` and
     `trace_path=f"{trace_dir}/trace_{case_id}_{pattern}_{run}.jsonl"`,
     starting the file empty, using the pattern's step function and
     starting state from `PATTERNS` and `GRANTED_FULL`;
   - check the outcome and the process, then record a row:
     `{"case", "pattern", "run", "status", "calls", "outcome_ok",
     "process_ok", "passed", "detail"}`. A run passes only if both checks
     pass. `detail` is `"ok"` if it passed; otherwise the failing checks'
     details, each prefixed `"outcome: "` or `"process: "`, joined with
     `"; "`.
   Return the rows in the order they ran.

5. **`compare_report(rows, cases)`** -- return a summary
   `{pattern: {case_id: {"passed": k, "runs": n, "mean_calls": m}}}`, with
   `mean_calls` the average of `calls` over that case's runs, rounded to 1
   decimal place. Print one line per case, in the order of `cases`, with
   each pattern's `passed/runs` and mean calls side by side, then a total
   line per pattern.

Run `python3 scaffold.py`. It loads the test set, runs both patterns on all
eight cases, prints your comparison, and lists every failure with its
detail. Then decide: did prediction 1 hold? Which cases did ReAct fail, and
what does the process check say about why?

## Optional extra: why pass rates?

`TEMPERATURE` near the top of the scaffold is 0, so runs repeat exactly.
Set it to `0.8` and run `run_test_set` with `runs=3`. Do any cases now pass
sometimes and fail other times? That is why the lecture said to report
`k` of `N`, never a single result. Set it back to 0 afterwards.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
