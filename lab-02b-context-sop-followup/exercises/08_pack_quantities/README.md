# Exercise 8 — Prompting for a Test Suite

Write `batch_pack_quantities(order_qty, pack_size)` in `starter.py`:
given how many units a customer ordered and how many units come in one
pack, return the number of packs needed to cover the order (you can
never ship a partial pack, so round up when the order doesn't divide
evenly). Prompt the assistant for an implementation, then prompt it for
a test suite. Run the tests against the implementation, then ask
yourself: does the test suite actually cover every kind of input you can
think of, including the ones that shouldn't be allowed at all? If not,
refine your prompt (ask for edge cases explicitly, ask what assumptions
it made) until it does. Record what you tried and why in `NOTES.md`.

Run `pytest` from inside this directory, not the repo root.

Before you start: quit any aider session left over from a previous
exercise and relaunch from here, or `/drop` files you no longer need.
This exercise doesn't depend on anything from Exercise 1-7.
