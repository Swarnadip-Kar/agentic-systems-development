# Exercise 4 — Prompting for a Test Suite

Write `merge_customer_records(records)` in `starter.py`: given a list of
dicts, each with a `customer_id` key and an `updated_at` timestamp
(among other fields), return one merged dict per `customer_id`, keeping
the values from whichever record has the most recent `updated_at` for
any overlapping fields. Prompt the assistant for an implementation, then
for a test suite. Run the tests against the implementation, then ask
yourself: does the test suite actually cover every assumption the
implementation might be making? If not, refine your prompt (ask for edge
cases explicitly, ask what assumptions it made) until it does. Record
what you tried and why in `NOTES.md`.

Run `pytest` from inside this directory, not the repo root.
