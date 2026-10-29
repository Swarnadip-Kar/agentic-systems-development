"""Oracle test for Q3 -- instructor/TA use only, never pushed to a
student repo."""
from q3_validate_decision import SupportDecision, validate_decision


def test_accepts_well_formed_decision():
    decision, error = validate_decision(
        '{"action": "escalate", "confidence": 0.9, "reason": "needs a human"}'
    )
    assert error is None
    assert decision.action == "escalate"
    assert decision.confidence == 0.9


def test_rejects_unknown_action():
    decision, error = validate_decision(
        '{"action": "cancel", "confidence": 0.9, "reason": "not a real action"}'
    )
    assert decision is None
    assert error is not None
    assert "json" not in error.lower()


def test_rejects_confidence_above_one():
    decision, error = validate_decision(
        '{"action": "escalate", "confidence": 1.5, "reason": "too confident"}'
    )
    assert decision is None
    assert error is not None


def test_accepts_confidence_boundary_values_for_a_non_refund_action():
    for value in (0.0, 1.0):
        decision, error = validate_decision(
            f'{{"action": "close", "confidence": {value}, "reason": "boundary"}}'
        )
        assert error is None
        assert decision.confidence == value


def test_reports_malformed_json_distinctly_from_schema_violation():
    decision, error = validate_decision("this is not json at all {broken")
    assert decision is None
    assert "json" in error.lower()


def test_rejects_refund_decision_with_low_confidence():
    decision, error = validate_decision(
        '{"action": "refund", "confidence": 0.3, "reason": "maybe a refund"}'
    )
    assert decision is None
    assert error is not None


def test_accepts_refund_decision_at_the_confidence_boundary():
    decision, error = validate_decision(
        '{"action": "refund", "confidence": 0.5, "reason": "clear duplicate charge"}'
    )
    assert error is None
    assert decision.action == "refund"
    assert decision.confidence == 0.5


def test_rejects_refund_decision_just_below_the_confidence_boundary():
    decision, error = validate_decision(
        '{"action": "refund", "confidence": 0.49, "reason": "just under"}'
    )
    assert decision is None
    assert error is not None


def test_rejects_top_level_json_that_is_not_an_object():
    decision, error = validate_decision("[1, 2, 3]")
    assert decision is None
    assert "json" not in error.lower()


def test_ignores_unknown_extra_fields():
    decision, error = validate_decision(
        '{"action": "close", "confidence": 0.9, "reason": "ok", "priority": "high"}'
    )
    assert error is None
    assert decision.action == "close"
