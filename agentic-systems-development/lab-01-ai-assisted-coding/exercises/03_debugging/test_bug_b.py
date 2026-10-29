from bug_b import safe_get


def test_key_present():
    assert safe_get({"a": 1}, "a") == 1


def test_key_missing_returns_default():
    assert safe_get({"a": 1}, "b", default="none") == "none"


def test_key_missing_no_default():
    assert safe_get({"a": 1}, "b") is None
