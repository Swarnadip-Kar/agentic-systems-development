"""Oracle test for Q5 -- instructor/TA use only, never pushed to a
student repo."""
from q5_permissions import check_permission


def test_allows_an_action_whose_exact_permission_is_granted():
    ok, error = check_permission("search_tickets", {"read"})
    assert ok is True
    assert error is None


def test_write_permission_implies_read():
    ok, error = check_permission("search_tickets", {"write"})
    assert ok is True


def test_admin_permission_implies_write_and_read():
    ok, error = check_permission("refund_ticket", {"admin"})
    assert ok is True


def test_read_permission_does_not_imply_write():
    ok, error = check_permission("refund_ticket", {"read"})
    assert ok is False
    assert "permission" in error.lower()


def test_rejects_an_unknown_action():
    ok, error = check_permission("delete_everything", {"admin"})
    assert ok is False
    assert "unknown" in error.lower()


def test_empty_granted_set_denies_any_permissioned_action():
    ok, error = check_permission("search_tickets", set())
    assert ok is False


def test_write_permission_does_not_imply_admin():
    ok, error = check_permission("delete_ticket", {"write"})
    assert ok is False
    assert "permission" in error.lower()
