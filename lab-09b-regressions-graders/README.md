# Lab 9b: Regressions and Grading the Grader

Builds on Lab 9a and Week 9's lecture, "Tests for Agents". `aider` is
available for this session.

## The idea

Lab 9a gave you tests for your agent. This lab uses them for the two jobs
the lecture ended on.

- **A change is safe only if no case gets worse.** A higher total can hide
  a case that used to pass and now fails. That is a regression, and the way
  to find it is to compare versions case by case.
- **A grader is trustworthy only if it agrees with people.** Some answers,
  like free-text replies from the runbook, cannot be checked with `==`. A
  model can grade them against a rubric, but a grader can be wrong, so you
  test it the same way: answers labelled by a person first, then a count of
  how often the grader agrees.

You will check the lecture's last two predictions:

> 2. Your planner on the smaller `aux` model plans worse: comparing it with
>    the planner on `main` shows regressions, case by case.
>
> 3. A smaller model is a worse grader: it agrees with your labels less
>    often than the larger one.

## What is given

Your Lab 9a evaluation harness (`load_test_set`, `check_outcome`,
`check_process`, `run_test_set`, `compare_report`) and everything it used.
`PATTERNS` now has a third version, `"plan-execute-on-aux"`: your planner
running on the smaller model. `test_set.json` is Lab 9a's, with all eight
answers. `runbook.json` is Lab 8b's runbook. `answers.json` holds ten
answers to runbook questions, unlabelled. `grader_messages(item, rubric)`
builds the two messages a grader sees.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace.
`call-flow.pdf` in this repo maps who calls whom. Keep it open.

## Exercises

1. **`regression_check(summary, cases, baseline, candidate)`** -- `summary`
   is what `compare_report` returns. Return the ids of the cases, in the
   order of `cases`, where the candidate's pass rate (`passed / runs`) is
   lower than the baseline's. A case that improved, or stayed the same, is
   not a regression.

2. **`run_regression(client, cases, baseline="plan-execute", candidate="plan-execute-on-aux", runs=1, trace_dir=".")`**
   -- run both versions over the test set with `run_test_set`, make the
   summary with `compare_report`, and find the regressions with
   `regression_check`. Print one line per case: its id, the baseline's and
   candidate's `passed/runs`, and `REGRESSION` or `ok`. Then print one
   verdict line: how many cases got worse, and `Do not ship this change.` if
   any did. Return `{"summary": ..., "regressions": [...]}`.

3. **Label the answers yourself, before any grader runs.**
   - In `answers.json`, read each answer against `runbook.json` and set
     `"label"` to `"pass"` or `"fail"`, with a one-line `"reason"`. An
     answer passes only if every claim it makes agrees with the runbook, it
     adds nothing the runbook does not say, and it answers the question (or
     says plainly that the runbook does not cover it).
   - **`load_labels(path="answers.json")`** -- return
     `{answer_id: label}`. Raise `ValueError` naming the answer's `id` if
     any label is not `"pass"` or `"fail"`, or any `reason` is empty. As in
     Lab 9a, a test set without answers does not run.

4. **Write the grader.**
   - **`RUBRIC`** -- replace the empty string with your rubric: the
     criteria a grader must check, and when the verdict is pass. Write it
     for the grader, not for a person.
   - **`build_verdict_schema()`** -- the JSON schema for the grader's
     reply: an object with a required `"verdict"` that must be `"pass"` or
     `"fail"` (use `"enum"`) and a required string `"reason"`. You may add
     a boolean for each of your criteria.
   - **`grade_answer(item, client, model)`** -- one model call with
     `model=model`, `temperature=0`,
     `messages=grader_messages(item, RUBRIC)`, and
     `response_format={"type": "json_schema", "json_schema": {"name":
     "grade", "schema": build_verdict_schema()}}`. Return the parsed reply
     as a dict.

5. **`grade_the_graders(client, answers, labels, graders=("aux", "main"))`**
   -- for each grader model, grade every answer with `grade_answer`, using
   `CountingClient(client)`. Count how many verdicts match your labels, and
   list the ids where they differ, in the order of `answers`. Print each
   grader's agreement, and each disagreement with the answer's id, the
   grader's verdict, and yours. Return
   `{model: {"agree": k, "total": n, "disagreements": [ids]}}`.

Run `python3 scaffold.py`. It runs the regression check, then grades your
labelled answers with both models. Then decide: did predictions 2 and 3
hold? For every disagreement, ask whether the grader is wrong, or your
label.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
