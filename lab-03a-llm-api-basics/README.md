# Lab 3a: LLM API Basics

Hand-written exercise -- write this file's logic yourself. `aider` is
available for debugging help (e.g. "why is this raising a KeyError"), but
not for generating the TODOs' implementations. Lab 3b, next session,
brings `aider` back to build on top of what you write here.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment, pointing at the course gateway. Pass `model="main"` to
`client.chat.completions.create()`.

## Exercises

Open `scaffold.py` and fill in each `TODO` in order:

1. **`get_client`** -- construct the API client.
2. **`classify_ticket`** -- make the raw request/response call.
3. **`extract_category`** -- parse the category out of the response.
   Some tickets get the model to hedge or explain rather than answer with
   a bare word (e.g. "I'd say this is billing, though it's technical
   too") -- a plain equality check will fail on these; you need to search
   the response text for whichever `ALLOWED_CATEGORIES` word appears.
4. **`classify_ticket_safely`** -- handle empty input, malformed
   responses, and real `openai` SDK errors (`RateLimitError`,
   `APITimeoutError`, `APIError`) without crashing.
5. **Bonus, `suggest_next_action`** -- ask the model for a next-action
   suggestion. No grading weight beyond attempting it; a preview of
   Week 5.

Run `python3 scaffold.py` after each TODO to check your progress against
the ticket set in `tickets.json`.

## Exercise 6: `REPORT.md` (trace-tied evidence)

Once `classify_ticket_safely` works, find your assigned trap ticket:

```python
import scaffold
scaffold.assigned_trap_ticket_id()
```

Run your code against that ticket's text (from `tickets.json`), then fill
in `REPORT.md`:

1. Paste the **literal raw completion text** you received for that ticket
   (whatever the model actually returned -- don't clean it up).
2. In one sentence, say which line/branch in `classify_ticket_safely`
   handles that response.

This is checked automatically against your own gateway log for that
ticket, not by a TA. It's a small, soft part of the grade (see below) --
the point is to show you actually ran your code against a real response,
not to catch anyone out.

## Grading

- **`test_scaffold.py` passing is the primary grade (~85-90%).** Your
  gateway trace (every call you make) is also logged automatically and
  checked for anomalies — code that "arrived complete" with
  disproportionately few matching gateway calls is flagged for instructor
  review.
- **`REPORT.md` is a small, soft part of the grade (~10-15%).** A
  missing or non-matching entry only costs this slice, never your
  correctness score, and is never an automatic penalty on its own.
