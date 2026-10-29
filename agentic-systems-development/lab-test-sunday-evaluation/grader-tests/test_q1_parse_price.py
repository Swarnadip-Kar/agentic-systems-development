"""Oracle test for Q1 -- instructor/TA use only, never pushed to a
student repo."""
import pytest

from q1_parse_price import parse_price


def test_extracts_a_simple_dollar_amount():
    assert parse_price("The total comes to $42.50 for your order.") == 42.50


def test_extracts_a_whole_dollar_amount_with_no_cents():
    assert parse_price("That will be $9 today.") == 9.0


def test_extracts_a_comma_grouped_amount():
    assert parse_price("Total: $1,234.56 due") == 1234.56


def test_extracts_the_first_amount_when_several_numbers_are_present():
    assert parse_price("Total: $1234.56 due, order #42 of 7 items.") == 1234.56


def test_raises_value_error_when_no_price_is_present():
    with pytest.raises(ValueError):
        parse_price("no price mentioned here at all")


def test_raises_value_error_on_empty_string():
    with pytest.raises(ValueError):
        parse_price("")
