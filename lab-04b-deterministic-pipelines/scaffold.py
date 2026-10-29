"""Lab 4b: deterministic wrappers and pipeline integration, aider-
assisted -- build on Lab 4a's schema and validation to make it
retry-until-valid, then feed the result into a routing pipeline."""
import json
import os
import time
from collections import defaultdict
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, Field, ValidationError, field_validator

ALLOWED_CATEGORIES = {"billing", "technical", "account", "feature-request", "complaint"}
MAX_ATTEMPTS = 4
MAX_VALIDATION_ATTEMPTS = 3
CONFIDENCE_ESCALATION_THRESHOLD = 0.7

# Synthetic responses for Exercise 4's retry-stats demonstration --
# deliberately includes some invalid-then-valid sequences so the
# retry mechanism has something real to report on every run. A live
# batch alone will usually show 0 retries (see Lab 4a's
# LENIENT_DEMO_RESPONSES for the same idiom and rationale).
RETRY_DEMO_SEQUENCES = [
    (201, ['{"category": "shipping", "confidence": 0.6, "reasoning": "wrong"}',
           '{"category": "billing", "confidence": 0.8, "reasoning": "corrected"}']),
    (202, ['{"category": "billing", "confidence": 0.9, "reasoning": "first try"}']),
    (203, ['{"category": "shipping", "confidence": 0.5, "reasoning": "wrong"}',
           '{"category": "shipping", "confidence": 0.5, "reasoning": "still wrong"}',
           '{"category": "technical", "confidence": 0.7, "reasoning": "corrected on last attempt"}']),
]


def _demo_retry_stats():
    # Feeds RETRY_DEMO_SEQUENCES through the same validate_classification
    # used by the real pipeline, recording how many raw responses each
    # synthetic ticket needed before one validated successfully -- same
    # (id, classification, attempts) shape classify_batch_deterministic
    # produces, so retry_stats_report can consume it unchanged.
    recorded = []
    for (ticket_id, responses) in RETRY_DEMO_SEQUENCES:
        for (attempt, raw) in enumerate(responses, start=1):
            classification, error = validate_classification(raw)
            if classification is not None:
                recorded.append((ticket_id, classification, attempt))
                break
    return recorded


def load_tickets_batch():
    data = json.loads(Path(__file__).with_name("tickets_batch.json").read_text())
    return data


def get_client():
    # max_retries=0: the openai SDK retries transient errors internally by
    # default (2 retries), which would silently swallow the failures this
    # exercise needs YOUR call_with_retry to actually see and handle.
    return OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
        max_retries=0,
    )


def call_with_retry(client, messages):
    for attempt in range(MAX_ATTEMPTS):
        try:
            return client.chat.completions.create(model="main", messages=messages)
        except (RateLimitError, APIError):
            if attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(2 ** attempt)


class TicketClassification(BaseModel):
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

    @field_validator("category")
    @classmethod
    def category_must_be_allowed(cls, v):
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(ALLOWED_CATEGORIES)} (got {v!r})")
        return v


def classify_with_schema(client, ticket_text):
    prompt = (
        "Classify this support ticket. Respond with ONLY a JSON object "
        f"with exactly these fields: category (one of {sorted(ALLOWED_CATEGORIES)}), "
        "confidence (a number between 0.0 and 1.0), reasoning (a short string). "
        f"Ticket: {ticket_text}"
    )
    response = call_with_retry(client, [{"role": "user", "content": prompt}])
    return response.choices[0].message.content


def validate_classification(raw_response_text):
    try:
        data = json.loads(raw_response_text)
    except json.JSONDecodeError as e:
        return None, f"response was not valid JSON: {e}"
    try:
        return TicketClassification(**data), None
    except ValidationError as e:
        return None, f"response failed schema validation: {e}"


def get_validated_classification(client, ticket_text):
    for attempt in range(MAX_VALIDATION_ATTEMPTS):
        raw_response_text = classify_with_schema(client, ticket_text)
        classification, error = validate_classification(raw_response_text)
        if classification is not None:
            return classification
        else:
            prompt = (
                f"Your previous response was invalid: {error}. "
                "Please provide a valid JSON object with the correct fields."
            )
            response = call_with_retry(client, [{"role": "user", "content": prompt}])
            raw_response_text = response.choices[0].message.content
    raise ValueError(f"Failed to get a valid classification after {MAX_VALIDATION_ATTEMPTS} attempts.")


def classify_batch_deterministic(client, tickets):
    recorded = []
    for ticket in tickets:
        ticket_id = ticket["id"]
        ticket_text = ticket["text"]
        try:
            classification = get_validated_classification(client, ticket_text)
            recorded.append((ticket_id, classification, 1, ticket_text))
        except ValueError as e:
            recorded.append((ticket_id, None, MAX_VALIDATION_ATTEMPTS, ticket_text))
            print(f"Ticket {ticket_id} failed to classify: {e}")
    return recorded


def routing_report(recorded):
    categorized_tickets = defaultdict(list)
    for ticket_id, classification, attempts, ticket_text in recorded:
        if classification:
            categorized_tickets[classification.category].append((ticket_id, classification.reasoning, classification.confidence, ticket_text))
    
    print("Routing Report:")
    for category, tickets in categorized_tickets.items():
        print(f"Category: {category}")
        for ticket_id, reasoning, confidence, ticket_text in tickets:
            print(f"  Ticket ID: {ticket_id}, Confidence: {confidence:.2f}, Reasoning: {reasoning}, Ticket Text: {ticket_text[:100]}...")

def escalation_export(recorded, out_path="escalation_queue.json"):
    low_confidence_tickets = []
    for ticket_id, classification, attempts, ticket_text in recorded:
        if classification and classification.confidence < CONFIDENCE_ESCALATION_THRESHOLD:
            low_confidence_tickets.append({
                "id": ticket_id,
                "classification": classification.dict(),
                "attempts": attempts,
                "ticket_text": ticket_text
            })
    
    if low_confidence_tickets:
        with open(out_path, "w") as f:
            json.dump(low_confidence_tickets, f, indent=2)
        print(f"Exported {len(low_confidence_tickets)} low-confidence tickets to {out_path}")


def retry_stats_report(recorded):
    total_attempts = sum(item[2] for item in recorded)
    successful_classifications = sum(1 for item in recorded if item[1] is not None)
    average_attempts_per_ticket = total_attempts / len(recorded) if recorded else 0
    
    print(f"Total Tickets Processed: {len(recorded)}")
    print(f"Successful Classifications: {successful_classifications}")
    print(f"Average Attempts per Ticket: {average_attempts_per_ticket:.2f}")


def main():
    client = get_client()
    tickets = load_tickets_batch()
    recorded = classify_batch_deterministic(client, tickets)
    routing_report(recorded)
    escalation_export(recorded)
    retry_stats_report(recorded)
    print("\n--- Retry-stats demonstration (synthetic responses, see README) ---")
    retry_stats_report(_demo_retry_stats())


if __name__ == "__main__":
    main()
