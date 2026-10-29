from bug_c import append_to_log


def test_fresh_log_starts_empty_then_has_one_item():
    log = append_to_log("first call")
    assert log == ["first call"]


def test_second_independent_call():
    log = append_to_log("second call, independent")
    assert log == ["second call, independent"]


def test_explicit_log_is_still_respected():
    my_log = ["existing"]
    result = append_to_log("new", log=my_log)
    assert result == ["existing", "new"]
