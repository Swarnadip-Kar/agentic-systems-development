"""Lab 4a: structured outputs and validation, aider-assisted -- same
tickets_batch.json domain as Lab 3b, now making the model's response a
validated structure instead of a trusted raw string."""
import json
import os
import time
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, Field, ValidationError, field_validator

ALLOWED_CATEGORIES = {"billing", "technical", "account", "feature-request", "complaint"}
MAX_ATTEMPTS = 4

# Synthetic near-miss raw responses for Exercise 5's strict-vs-lenient
# comparison -- deliberately NOT live model output. A well-prompted
# model reliably returns exact-match categories, so a live comparison
# would show zero recovered tickets every run (see the README's note
# on why this fixture exists, same idiom as Lab 3b's artificial
# MAX_CONTEXT_TOKENS budget). Ticket ids here are synthetic, not from
# tickets_batch.json.
LENIENT_DEMO_RESPONSES = [
    (101, '{"category": "Billing", "confidence": 0.85, "reasoning": "mentions an invoice"}'),
    (102, '{"category": " technical ", "confidence": 0.7, "reasoning": "app crash reported"}'),
    (103, '{"category": "ACCOUNT", "confidence": 0.9, "reasoning": "login issue"}'),
    (104, '{"category": "shipping", "confidence": 0.6, "reasoning": "not a real category"}'),
]


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
    category: str = Field(..., description="one of billing, technical, account, feature-request, complaint")
    confidence: float = Field(..., ge=0.0, le=1.0, description="between 0.0 and 1.0 inclusive")
    reasoning: str = Field(..., min_length=1, description="short string")

    @field_validator('category')
    def check_category(cls, v):
        if v.lower().strip() not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category: {v}. Must be one of {', '.join(ALLOWED_CATEGORIES)}")
        return v.lower().strip()


def classify_with_schema(client, ticket_text):
    # Actual Prompt
    prompt = (
        "Classify this support ticket. Respond with "
        "ONLY a JSON object with exactly these fields: "
        "category (one of billing, technical, account, feature-request, complaint), "
        "confidence (0.0 - 1.0), "
        "reasoning (a short string)."
    )

    # # Vauge Prompt
    # prompt = (
    #     " Respond with ONLY a JSON object with exactly "
    #     " these fields : category (one of billing, technical, account, feature-request, complaint) , "
    #     " confidence (0.0 -1.0) , reasoning ."
    # )

    # # Extremely vauge system prompt
    # prompt = ("JSON Object")

    # # Wrong Structure -> Confidence removed.
    # prompt = (
    #     "Classify this support ticket. Respond with "
    #     "ONLY a JSON object with exactly these fields: "
    #     "category (one of billing, technical, account, feature-request, complaint), "
    #     "reasoning (a short string)."
    # )

    # # Wrong Structure -> Not a JSON Object
    # prompt = (
    #     "Classify this support ticket. Respond with "
    #     "with exactly these fields: "
    #     "category (one of billing, technical, account, feature-request, complaint), "
    # )

    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": ticket_text}]
    response = call_with_retry(client, messages)
    return response.choices[0].message.content


def validate_classification(raw_response_text):
    try:
        data = json.loads(raw_response_text)
        classification = TicketClassification(**data)
        if not classification.reasoning.strip():
            raise ValueError("Reasoning must not be empty")
        return classification, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    except ValidationError as e:
        return None, f"Validation error: {e}"


def classify_batch_with_validation(client, tickets):
    results = []
    for ticket in tickets:
        raw_response_text = classify_with_schema(client, ticket["text"])
        classification, error = validate_classification(raw_response_text)
        results.append((ticket["id"], classification, error))
    
    total_tickets = len(tickets)
    successful_tickets = sum(1 for _, _, error in results if error is None)
    success_rate = (successful_tickets / total_tickets) * 100
    print(f"{successful_tickets}/{total_tickets} tickets validated successfully ({success_rate:.2f}%)")
    
    for ticket_id, classification, error in results:
        print(f"Ticket ID: {ticket_id}")
        print(f"Raw Response: {raw_response_text}")
        if error:
            print(f"Error: {error}")
        else:
            print("Classification:")
            print(f"  Category: {classification.category}")
            print(f"  Confidence: {classification.confidence}")
            print(f"  Reasoning: {classification.reasoning}")
        print("-" * 40)
    
    return results


class LenientTicketClassification(BaseModel):
    category: str = Field(..., description="one of billing, technical, account, feature-request, complaint")
    confidence: float = Field(..., ge=0.0, le=1.0, description="between 0.0 and 1.0 inclusive")
    reasoning: str = Field(..., min_length=1, description="short string")

    @field_validator('category')
    def check_category(cls, v):
        v = v.lower().strip()
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category: {v}. Must be one of {', '.join(ALLOWED_CATEGORIES)}")
        return v


def strict_vs_lenient_report(tickets, strict_failures, lenient_failures):
    strict_failure_count = len(strict_failures)
    lenient_failure_count = len(lenient_failures)

    print(f"Strict failures: {strict_failure_count}")
    print(f"Lenient failures: {lenient_failure_count}")

    strict_failure_ids = set(ticket_id for ticket_id, _ in strict_failures)
    lenient_failure_ids = set(ticket_id for ticket_id, _ in lenient_failures)

    recovered_tickets = strict_failure_ids - lenient_failure_ids

    if recovered_tickets:
        print("Tickets recovered by lenient normalization:")
        for ticket_id in recovered_tickets:
            print(f"  Ticket ID: {ticket_id}")
    else:
        print("No tickets were recovered by lenient normalization.")


def main():
    client = get_client()
    tickets = load_tickets_batch()
    recorded = classify_batch_with_validation(client, tickets)

    strict_failures = []
    lenient_failures = []
    for (ticket_id, raw) in LENIENT_DEMO_RESPONSES:
        try:
            data = json.loads(raw)
            TicketClassification(**data)
        except Exception as e:
            strict_failures.append((ticket_id, str(e)))
        try:
            data = json.loads(raw)
            LenientTicketClassification(**data)
        except Exception as e:
            lenient_failures.append((ticket_id, str(e)))

    strict_vs_lenient_report(tickets, strict_failures, lenient_failures)


if __name__ == "__main__":
    main()
