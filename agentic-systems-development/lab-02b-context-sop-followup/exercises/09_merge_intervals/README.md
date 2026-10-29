# Exercise 9 — Prompting for a Test Suite

Write `merge_overlapping_intervals(intervals)` in `starter.py`: given a
list of `(start, end)` tuples, merge any that overlap or touch, and
return the merged list of non-overlapping intervals. Prompt the
assistant for an implementation, then prompt it for a test suite. Run
the tests against the implementation, then ask yourself: does the test
suite actually cover every assumption the implementation might be
making about the input, including the order it arrives in? If not,
refine your prompt (ask for edge cases explicitly, ask what assumptions
it made) until it does. Record what you tried and why in `NOTES.md`.

Run `pytest` from inside this directory, not the repo root.

Before you start: quit any aider session left over from a previous
exercise and relaunch from here, or `/drop` files you no longer need.
This exercise doesn't depend on anything from Exercise 1-8.
