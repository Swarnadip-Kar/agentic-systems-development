# Lab 3b: Conversation State and Retries

Builds directly on Lab 3a's scaffold. `aider` is available for this
session -- use it to help implement the TODOs in `scaffold.py`.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

## Exercises

1. **`call_with_retry`** -- wrap a single API call with exponential
   backoff on transient failures.
2. **`classify_batch`** -- classify every ticket in `tickets_batch.json`
   inside ONE growing conversation, carrying history across calls.
3. **`token_growth_report`** -- report how the conversation history grows
   across the batch, and connect it back to the Lab 2 bottleneck.
4. **`check_budget`** -- diagnose: given the growth from Exercise 3, find
   the first ticket that pushes the conversation over a token budget.
5. **`enforce_budget`** -- treat: once you know growth is a problem,
   trim the conversation's oldest turns to stay near budget, and watch
   how that changes `classify_batch`'s behavior on the remaining
   tickets.

**Why the budget (`MAX_CONTEXT_TOKENS = 300`) is so low:** the real
model's context window is far larger than 8 short exchanges could ever
fill. We've set an artificial limit here so the mechanism -- detect
growth, respond to it -- is something you can actually trigger and
observe in one lab session. The technique (track usage, trim or
summarize when you approach a limit) is exactly what production systems
do at real scale, just with a much bigger number.

**Bonus (ungraded, optional):** `summarize_and_replace` in `scaffold.py`
is a stretch goal if you finish early -- instead of dropping old turns
like `enforce_budget`, it asks the model to summarize them into one
condensed message. Closer to what production systems actually do; try
it and compare.

Run `python3 scaffold.py` to check your progress.

**You will see real `RateLimitError`s during this lab.** They're
intentional, not a bug in your code or the course infrastructure --
`call_with_retry` needs a genuine failure to actually catch, and a batch
of 8 sequential tickets is too small to ever trip a real rate limit
naturally. If your `call_with_retry` isn't implemented (or isn't
implemented correctly), `scaffold.py` will crash with an unhandled
`RateLimitError` partway through the batch -- that's the exercise working
as intended, not something to work around.

## Grading

Same gateway-trace logging and anomaly-based checking as Lab 3a.
