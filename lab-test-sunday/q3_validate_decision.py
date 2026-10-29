"""Q3: validate a model's JSON decision against a schema, with a
cross-field rule.

Aider: NOT ALLOWED for this question. Using Aider, or any AI
code-generation assistant, to write your solution here means this
question will not be evaluated.
"""
import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


LENIENT_DEMO_RESPONSES = [
    (101, '{"category": "refund", "confidence": 0.85, "reason": "mentions an invoice"}'),
    (102, '{"category": "refund", "confidence": 0.1, "reason": "app crash reported"}'),
    (103, '{"category": "escalate", "confidence": 0.9, "reason": "login issue"}'),
    (104, '{"category": "close", "confidence": 0.6, "reason": "not a real category"}'),
    (105, 'ory": "close", "confidence": 0.6, "reason": "not a real category"}'), #invalid schema
]

class SupportDecision(BaseModel):
    """A support-ticket decision. action must be one of "refund",
    "escalate", "close". confidence must be between 0.0 and 1.0
    inclusive. Additionally: a "refund" action needs confidence >= 0.5
    -- a low-confidence refund should be rejected, not just recorded."""
    action: Literal["refund", "escalate", "close"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str

    @model_validator(mode="after")
    def refund_needs_high_confidence(self):
        """Raise ValueError if action == "refund" and confidence < 0.5.
        Otherwise return self."""
        if action == "refund" and confidence < 0.5:
            raise ValueError(f"Refund Confidence should be >=0.5")
        return self


def validate_decision(raw):
    """Parse `raw` (a JSON string) into a SupportDecision.

    Return (decision, None) on success, or (None, error_message) on
    failure. If `raw` is not valid JSON at all, error_message must
    contain the word "json" (case-insensitive). If it parses but
    violates the schema (including the refund/confidence rule above),
    error_message must NOT contain "json".
    """
    try:
        data = json.loads(raw_response_text)
        classification = SupportDecision(**data)
        return classification, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    except ValidationError as e:
        return None, f"Validation error: {e}"