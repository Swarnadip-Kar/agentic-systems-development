# Lab 10: Debugging Your Own Agent from Its Traces

Builds on Week 10's lecture, "Observability, Traces, and Debugging".
`aider` is available for this session.

## The idea

Last week's tests told you **that** a case failed. This week the question
is **why**. The lecture's bug never raised an exception: the run ended
with `status: "done"` and still did the wrong thing. You only find a bug
like that by reading what the agent actually did, step by step, in its
trace, and finding the first place it left the path it should have taken.

You do it on **your own agent**. The two broken files in this repo are
your own Lab 9a `scaffold.py`, with your own `load_test_set`,
`check_outcome`, `check_process`, `run_test_set` and `compare_report`.
Into each one, a single bug has been injected somewhere in the **given**
part of the file, above the `# --- your work ---` marker. Your own code
below the marker is untouched. Because every student's agent is their
own, your traces will not look like your neighbour's.

The rule for this lab: **diagnose from the trace first, then fix.** Write
down where the run diverged before you change a line.

## What is given

- `scaffold_bug_a.py` and `scaffold_bug_b.py` -- your Lab 9a scaffold,
  one bug in each. They are separate on purpose: one failure never hides
  the other.
- `test_set.json` -- your own eight test cases from Lab 9a.
- `tickets.json` -- the ticket world, unchanged.
- `diagnose.py` -- a stub for Exercise 1.
- `lab10.py` -- a runner (given, do not edit). It runs your own harness
  with your planner (`plan-execute`) against whichever scaffold file you
  name, and writes the files you commit:

  ```
  python3 lab10.py run <scaffold_file> <case_id> <trace_out.jsonl>
  python3 lab10.py diagnose <trace.jsonl> <diagnosis_out.json>
  python3 lab10.py sweep <scaffold_file> <rows_out.json>
  ```

  `diagnose` calls your `diagnose_divergence` with the expected shape
  `["get_ticket_history", "escalate_ticket"]`: read the ticket's history,
  then escalate.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace.
Every command above makes real model calls through the gateway, paced
under its 30 calls a minute, so a sweep takes a few minutes. Run from the
repo's top directory.

## Exercises

1. **`diagnose_divergence(trace, expected_shape)`** in `diagnose.py`.
   The docstring gives the trace format and the exact return value. A
   call counts only if its result has no `"error"`. Walk
   `expected_shape` in order through the counted calls, matching each
   expected tool to its **earliest** counted call after the previous
   match; report the first expected tool that never happened, and the
   step where the expected tool before it was matched.

2. **Bug A: diagnose, then fix.**
   - `python3 lab10.py run scaffold_bug_a.py escalate-never-escalated trace_bug_a.jsonl`
   - `python3 lab10.py diagnose trace_bug_a.jsonl diagnosis_bug_a.json`
     -- **before** you change anything in `scaffold_bug_a.py`.
   - `python3 lab10.py sweep scaffold_bug_a.py sweep_bug_a_before.json`
     -- the bug across all eight cases, still unfixed.
   - Now read the trace and the diagnosis, find the bug in the given part
     of `scaffold_bug_a.py`, and fix it. Do not touch your own code below
     the marker.
   - `python3 lab10.py run scaffold_bug_a.py escalate-never-escalated trace_bug_a_fixed.jsonl`
     -- a fresh trace that shows the case passing.

3. **Bug B: the same, for `scaffold_bug_b.py`.** Same case, same steps,
   with the files `trace_bug_b.jsonl`, `diagnosis_bug_b.json`,
   `sweep_bug_b_before.json`, and `trace_bug_b_fixed.jsonl`. Hint: the
   diagnosis names a tool that never succeeded. Look at what the given
   code does when that tool is called.

4. **At scale.** After both fixes:
   - `python3 lab10.py sweep scaffold_bug_a.py sweep_bug_a_after.json`
   - `python3 lab10.py sweep scaffold_bug_b.py sweep_bug_b_after.json`

   Compare each `_before` sweep with its `_after` sweep: bugs active
   against bugs fixed, across all eight cases, not one anecdote. Which
   cases did each bug break, and did every one of them recover?

Commit and push everything: `diagnose.py`, both fixed scaffold files,
and all `trace_*.jsonl`, `diagnosis_*.json` and `sweep_*.json` files.

## Optional extra: loud and quiet failures

No new runs needed; use the files you already have. Look at the
`status` of the failing rows in `sweep_bug_a_before.json` and in
`sweep_bug_b_before.json`. One bug mostly ends runs `exhausted`; the
other ends them `done`. From your traces, why does one bug keep your
planner going until the round limit while the other lets it stop
early? Which of your two checks caught each failing case? And which kind
of failure would you rather meet in production, the one that runs out of
rounds or the one that reports `done`?

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
`diagnose_divergence` is tested on traces you have not seen. Each
`diagnosis_*.json` must match what your own `diagnose_divergence`
produces from the trace you committed next to it, and that trace must
come from the broken file, before the fix. A diagnosis that does not come
from its trace costs that part of the grade.
