# Exercise 2 — Prompt Refinement

Implement `sort_names` in `starter.py`: given a list of name strings,
return a new list sorted alphabetically, **case-insensitively** — so
`"apple"`, `"Banana"`, and `"cherry"` sort as if everything were the same
case, regardless of actual capitalization.

```
sort_names(["banana", "Cherry", "apple"]) -> ["apple", "banana", "Cherry"]
```

This exercise is about the prompt, not the function — it's a one-line
function either way. Do it twice, deliberately:

## Round 1 — vague prompt

Ask the assistant something close to: *"write a function that sorts a
list of names alphabetically."* Don't mention case-sensitivity. See what
you get. Run the tests.

**Predict before you run them**: do you expect this to pass? Which test
do you think will fail, and why?

## Round 2 — refined prompt

Now write a prompt that states the actual requirement precisely: sorting
must be case-insensitive regardless of how each name is capitalized. Get
it working.

## Write it up

In the root `NOTES.md`, record your vague prompt, what came back and why
it was wrong (if it was), your refined prompt, and what changed. This is
the part that's actually graded here — the working function is table
stakes, the reflection on *why* the refinement mattered is the point of
the exercise.
