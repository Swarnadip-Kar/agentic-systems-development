# Lab 4c: Consensus Classification (Self-Consistency)

A short bonus session, same `tickets_batch.json` domain as Lab 4a/4b.
Instead of trusting one response (4a) or retrying a single call until
it validates (4b), this time you sample the model **multiple times
independently** for the same ticket and only trust the answer if the
independent samples agree with each other. `aider` is available.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

## Provided

- `classify_with_schema(client, ticket_text)` -- makes one classification
  call, returns the raw response text.
- `validate_classification(raw_response_text)` -- parses/validates one
  raw response against the `TicketClassification` schema, returns
  `(classification, error)`.
- `call_with_retry` / `TicketClassification` -- same as Lab 4a/4b.

## Exercises

1. **`get_consensus_classification(client, ticket_text, n_calls=CONSENSUS_CALLS)`**
   -- call `classify_with_schema` `n_calls` times **independently**
   (fresh calls, not retries of a failed one), and validate each raw
   response with `validate_classification`, discarding any that fail
   validation.

   A **consensus** exists only if a strict majority of the valid
   responses agree on the same `category` -- with `CONSENSUS_CALLS = 3`,
   that means at least 2 of the 3 valid responses must share a category.
   If a consensus category exists: build a `TicketClassification` for it
   with `confidence` set to the average confidence of the responses that
   agreed, and `reasoning` taken from the first agreeing response.
   Return `(classification, agree_count)` where `agree_count` is how
   many of the `n_calls` responses agreed on that category (2 or 3).

   If no category reaches a majority -- including when fewer than 2
   responses even validated -- there is **no consensus**. Return
   `(None, 0)` in that case; do not guess or pick a highest-confidence
   single answer.

2. **`classify_batch_with_consensus(client, tickets, n_calls=CONSENSUS_CALLS)`**
   -- call `get_consensus_classification` for every ticket in `tickets`.
   Record `(ticket["id"], classification, agree_count)` for every
   ticket -- `classification` may legitimately be `None` when no
   consensus was reached; that's an expected outcome here, not an
   error. Return the list of recorded tuples.

3. **`consensus_report(recorded)`** -- given the recorded list from
   Exercise 2, print a summary with three buckets: tickets with
   **unanimous** agreement (`agree_count == 3`), tickets with
   **majority** agreement (`agree_count == 2`), and tickets that
   **need escalation** (`classification is None`), e.g.:
   `"5/8 unanimous, 2/8 majority, 1/8 needs escalation (no consensus)"`.

`main()` runs your pipeline against the live batch, then separately runs
`consensus_report` over a small set of pre-built example results
(`CONSENSUS_DEMO_RECORDED`) covering all three buckets -- a well-prompted
model usually agrees with itself on this ticket batch, so a live-only
run would rarely show every bucket. Same idiom Lab 3b/4a/4b used for
their own synthetic fixtures.

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
