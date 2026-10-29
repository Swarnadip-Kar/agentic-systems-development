"""Lab 4c: consensus classification via repeated independent sampling --
same tickets_batch.json domain as Lab 4a/4b, now trusting agreement
across several independent model calls instead of a single validated
response."""
import json
import os
import time
from collections import Counter
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, Field, ValidationError, field_validator

ALLOWED_CATEGORIES = {"billing", "technical", "account", "feature-request", "complaint"}
MAX_ATTEMPTS = 4
CONSENSUS_CALLS = 3

# Pre-built (ticket_id, classification, agree_count) results covering all
# three consensus_report buckets -- deliberately NOT derived from live
# calls, same idiom as Lab 4a/4b's own demo fixtures (a well-prompted
# model usually agrees with itself, so a live-only run would rarely show
# every bucket).
CONSENSUS_DEMO_RECORDED = [
    (301, {"category": "billing", "confidence": 0.9, "reasoning": "invoice mismatch"}, 3),
    (302, {"category": "technical", "confidence": 0.775, "reasoning": "crash reported"}, 2),
    (303, None, 0),
]


def load_tickets_batch():
    data = json.loads(Path(__file__).with_name("tickets_batch.json").read_text())
    return data


def get_client():
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


def get_consensus_classification(client, ticket_text, n_calls=CONSENSUS_CALLS):
    valid_responses = []
    for _ in range(n_calls):
        raw_response = classify_with_schema(client, ticket_text)
        classification, error = validate_classification(raw_response)
        if classification is not None:
            valid_responses.append(classification)

    if len(valid_responses) < 2:
        return None, 0

    category_counts = Counter(response.category for response in valid_responses)
    most_common_category, agree_count = category_counts.most_common(1)[0]

    if agree_count >= (n_calls // 2) + 1:
        avg_confidence = sum(response.confidence for response in valid_responses) / agree_count
        return TicketClassification(category=most_common_category, confidence=avg_confidence, reasoning=valid_responses[0].reasoning), agree_count
    else:
        return None, 0


def classify_batch_with_consensus(client, tickets, n_calls=CONSENSUS_CALLS):
    results = []
    for ticket in tickets:
        classification, agree_count = get_consensus_classification(client, ticket["text"], n_calls)
        results.append((ticket["id"], classification, agree_count))
    return results


def consensus_report(recorded):
    unanimous_count = 0
    majority_count = 0
    escalation_count = 0

    for _, classification, agree_count in recorded:
        if classification is not None:
            if agree_count == 3:
                unanimous_count += 1
            elif agree_count == 2:
                majority_count += 1
        else:
            escalation_count += 1

    total_tickets = len(recorded)
    print(f"{unanimous_count}/{total_tickets} unanimous, {majority_count}/{total_tickets} majority, {escalation_count}/{total_tickets} needs escalation (no consensus)")


def main():
    client = get_client()
    tickets = load_tickets_batch()
    recorded = classify_batch_with_consensus(client, tickets)
    consensus_report(recorded)

    print("\n--- Consensus-report demonstration (pre-built examples, see README) ---")
    demo_recorded = [
        (ticket_id, TicketClassification(**data) if data is not None else None, agree_count)
        for (ticket_id, data, agree_count) in CONSENSUS_DEMO_RECORDED
    ]
    consensus_report(demo_recorded)


if __name__ == "__main__":
    main()
