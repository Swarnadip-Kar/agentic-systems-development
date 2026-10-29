"""Oracle test for Q6 -- instructor/TA use only, never pushed to a
student repo. dispatch() is pure and tested entirely with a fake
registry -- no network, matching the question's offline-grading
requirement; the one live call the question also asks for is never
part of grading."""
from q6_tool_dispatch import dispatch

REGISTRY = {
    "lookup_price": {
        "permission": "read",
        "fn": lambda sku: {"sku": sku, "price": 9.99} if sku == "A1" else {"error": "no such sku"},
    },
}


def test_dispatches_a_known_tool_with_granted_permission():
    result = dispatch("lookup_price", {"sku": "A1"}, REGISTRY, {"read"}, {})
    assert result == {"sku": "A1", "price": 9.99}


def test_denies_a_known_tool_without_the_right_permission():
    result = dispatch("lookup_price", {"sku": "A1"}, REGISTRY, set(), {})
    assert "error" in result
    assert "permission" in result["error"].lower()


def test_rejects_an_unknown_tool_name():
    result = dispatch("delete_everything", {}, REGISTRY, {"read", "write"}, {})
    assert "error" in result
    assert "unknown" in result["error"].lower()


def test_reports_a_dispatch_failure_instead_of_raising():
    result = dispatch("lookup_price", {"wrong_arg": "A1"}, REGISTRY, {"read"}, {})
    assert "error" in result


def test_allows_up_to_three_calls_then_denies_the_fourth():
    call_counts = {}
    for _ in range(3):
        result = dispatch("lookup_price", {"sku": "A1"}, REGISTRY, {"read"}, call_counts)
        assert result == {"sku": "A1", "price": 9.99}
    fourth = dispatch("lookup_price", {"sku": "A1"}, REGISTRY, {"read"}, call_counts)
    assert "error" in fourth
    assert "budget" in fourth["error"].lower()


def test_denied_calls_do_not_count_against_the_budget():
    call_counts = {}
    dispatch("lookup_price", {"sku": "A1"}, REGISTRY, set(), call_counts)  # permission denied
    dispatch("delete_everything", {}, REGISTRY, {"read"}, call_counts)    # unknown tool
    assert call_counts == {}


def test_a_failed_dispatch_still_consumes_a_budget_slot():
    call_counts = {}
    dispatch("lookup_price", {"wrong_arg": "A1"}, REGISTRY, {"read"}, call_counts)  # fails, TypeError path
    assert call_counts.get("lookup_price", 0) == 1
