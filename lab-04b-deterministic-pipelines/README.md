# Lab 4b: Deterministic Wrappers and Pipeline Integration

Builds directly on Lab 4a's schema and validation. `aider` is available
for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.

## Exercises

1. **`get_validated_classification`** -- the deterministic wrapper:
   retry with the specific validation error fed back to the model, up
   to `MAX_VALIDATION_ATTEMPTS` times, then raise clearly.
2. **`classify_batch_deterministic`** -- run Exercise 1 across the
   whole batch.
3. **`routing_report` + `escalation_export`** -- group validated
   tickets by category, flag low-confidence ones for human review
   instead of auto-routing, and export those to a separate JSON file --
   two consumers of the same validated data.
4. **`retry_stats_report`** -- report how many tickets needed a retry,
   concrete evidence of whether the error-feedback retry is helping.
   `main()` runs `retry_stats_report` over a small set of synthetic
   invalid-then-valid response sequences (`RETRY_DEMO_SEQUENCES`), not
   the live batch alone -- a well-prompted model rarely fails
   validation on the first try, so a live-only run would usually show
   zero retries. This is the same idiom Lab 3b used for its artificial
   token budget.

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
