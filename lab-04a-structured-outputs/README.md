# Lab 4a: Structured Outputs and Validation

Builds on Lab 3b's `tickets_batch.json` -- same tickets, new technique.
`aider` is available for this session.

## Setup

`OPENAI_BASE_URL` and `OPENAI_API_KEY` are already set in your workspace
environment. Pass `model="main"` to `client.chat.completions.create()`.
This lab adds `pydantic` as a dependency -- already installed in your
workspace.

## Exercises

1. **`TicketClassification`** -- define a Pydantic schema for a ticket
   classification response: `category` (must be one of
   `ALLOWED_CATEGORIES`), `confidence` (0.0-1.0), `reasoning`.
2. **`classify_with_schema`** -- prompt the model to return JSON
   matching that schema, and return the raw response text.
3. **`validate_classification`** -- parse and validate a raw response,
   distinguishing "not valid JSON at all" from "valid JSON but wrong
   shape."
4. **`classify_batch_with_validation`** -- run Exercises 2-3 across the
   whole batch, report a validation success rate. Also requires
   `reasoning` to be non-empty -- a schema-valid but empty-string
   `reasoning` counts as a failure here.
5. **`LenientTicketClassification` + `strict_vs_lenient_report`** --
   a normalizing variant of the schema (case/whitespace-insensitive
   category matching) and a report comparing how many tickets it
   recovers versus the strict schema. The strict-vs-lenient comparison
   in `main()` runs over a small set of deliberately messy synthetic
   responses (`LENIENT_DEMO_RESPONSES`), not live model output -- a
   well-prompted model reliably returns exact-match categories, so a
   live comparison would show nothing recovered. This mirrors Lab 3b's
   artificial token budget: the mechanism needs a guaranteed way to
   trigger in one session.

Run `python3 scaffold.py` to check your progress.

## Grading

Same gateway-trace logging and anomaly-based checking as prior labs.
