# Exercise 1 — First Prompt

Implement `parse_duration` in `starter.py`. It takes a short duration
string like `"1h30m"`, `"45m"`, or `"2h"` and returns the total number of
minutes as an integer.

```
parse_duration("1h30m") -> 90
parse_duration("45m")   -> 45
parse_duration("2h")    -> 120
```

## Steps

1. Run `aider exercises/01_first_prompt/starter.py exercises/01_first_prompt/test_starter.py`.
2. Describe the task to Aider in your own words — don't just paste this
   README. Include the examples above so the assistant has something
   concrete to match.
3. **Before accepting the diff, read it.** Does it handle `"45m"` (minutes
   only, no hours)? What does it do with `"2h"` (no minutes)? What happens
   on a malformed string like `"abc"` — does it crash predictably or
   silently return something wrong?
4. Run the tests: `pytest exercises/01_first_prompt/test_starter.py -v`
5. If something fails, that's normal — go back to the assistant with the
   specific failure, not a vague "fix it."
