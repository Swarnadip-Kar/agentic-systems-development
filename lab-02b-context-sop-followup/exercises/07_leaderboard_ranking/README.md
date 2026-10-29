# Exercise 7 — Prompting for a Test Suite

Write `rank_leaderboard(players)` in `starter.py`: given a list of
`(name, score)` tuples, return a list of `(name, rank)` tuples ranking
players from highest score to lowest, where `rank` starts at 1. Prompt
the assistant for an implementation, then prompt it for a test suite.
Run the tests against the implementation, then ask yourself: does the
test suite actually cover every assumption the implementation is making
about ties, or only the case where every score happens to be distinct?
If not, refine your prompt (ask for edge cases explicitly, ask what
assumptions it made) until it does. Record what you tried and why in
`NOTES.md`.

Run `pytest` from inside this directory, not the repo root.

Before you start: quit any aider session left over from a previous
exercise and relaunch from here, or `/drop` files you no longer need.
This exercise doesn't depend on anything from Exercise 1-6.
