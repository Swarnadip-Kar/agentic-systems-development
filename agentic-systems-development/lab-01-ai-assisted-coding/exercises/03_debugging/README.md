# Exercise 3 — Debugging with the Assistant

Three small files, each with one seeded bug and a failing test. For each:

1. Run the test first, read the failure.
2. Paste the failure (or describe it) to the assistant and ask it to
   diagnose — don't ask it to blindly "fix the code" without engaging with
   *why* it's wrong.
3. **Check whether its first diagnosis is actually correct** before
   applying a fix. Assistants sometimes propose a fix that makes the test
   pass for the wrong reason (e.g., papering over a symptom instead of the
   real bug, or hand-tuning to the specific test input). Read the fix.
4. Re-run the test to confirm.
5. Note in root `NOTES.md`: what you told the assistant, what it diagnosed,
   and whether that first diagnosis actually held up.

## Files

- `bug_a.py` — `moving_average`: off-by-one in a windowing calculation.
- `bug_b.py` — `safe_get`: catches the wrong exception type.
- `bug_c.py` — `append_to_log`: the classic mutable-default-argument trap.

Run all three at once: `pytest exercises/03_debugging/ -v`
