from starter import parse_duration


def test_hours_and_minutes():
    assert parse_duration("1h30m") == 90


def test_minutes_only():
    assert parse_duration("45m") == 45


def test_hours_only():
    assert parse_duration("2h") == 120


def test_zero_minutes():
    assert parse_duration("0m") == 0


def test_single_digit_hour_and_minutes():
    assert parse_duration("1h5m") == 65
