# Exercise 6 — Prompting for a Test Suite

Write `compute_late_fee(due_date, paid_date, daily_rate)` in
`starter.py`: given a due date and the date it was actually paid (both
`"YYYY-MM-DD"` strings) and a daily late-fee rate, return the total late
fee. Prompt the assistant for an implementation, then prompt it for a
test suite. Run the tests against the implementation, then ask yourself:
does the test suite actually bound every input the function could
receive, or only the input you happened to think of? If not, refine your
prompt (ask for edge cases explicitly, ask what assumptions it made)
until it does. Record what you tried and why in `NOTES.md`.

Run `pytest` from inside this directory, not the repo root.

Before you start: quit any aider session left over from a previous
exercise and relaunch from here, or `/drop` files you no longer need.
This exercise doesn't depend on anything from Exercise 1-5.
