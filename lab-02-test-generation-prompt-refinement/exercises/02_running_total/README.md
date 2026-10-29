# Exercise 2 — Prompting for a Test Suite

Write `get_running_total(transactions)` in `starter.py`: given a list of
dicts with `amount` and `type` keys (`type` is either `"credit"` or
`"debit"`), return a list of the running balance after each transaction.
Prompt the assistant for an implementation, then prompt it for a test
suite. Run the tests against the implementation, then ask yourself: do
the tests actually cover every kind of input you can think of? If not,
refine your prompt (ask for edge cases explicitly, ask what assumptions
it made) until they do. Record what you tried and why in `NOTES.md`.

Run `pytest` from inside this directory, not the repo root.
