# Exercise 5 — Prompting for a Test Suite

Write `redact_contact_info(text)` in `starter.py`: given a block of free
text, return a copy with any email addresses and phone numbers replaced
by `[REDACTED]`, leaving everything else unchanged. Prompt the assistant
for an implementation, then prompt it for a test suite. Run the tests
against the implementation, then ask yourself: do the tests actually
cover every kind of email/phone format you can think of, or only the one
format the assistant happened to pick? If not, refine your prompt (ask
for edge cases explicitly, ask what assumptions it made) until they do.
Record what you tried and why in `NOTES.md`.

Run `pytest` from inside this directory, not the repo root.

Before you start: quit any aider session left over from a previous
exercise and relaunch from here, or `/drop` files you no longer need.
This exercise doesn't depend on anything from Exercise 1-4.
