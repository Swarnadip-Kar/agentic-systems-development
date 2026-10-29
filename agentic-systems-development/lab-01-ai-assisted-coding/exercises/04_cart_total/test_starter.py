from starter import price_with_tax, cart_total


def test_price_with_tax_basic():
    assert price_with_tax(100.0, 10) == 110.0


def test_price_with_tax_rounds():
    assert price_with_tax(19.995, 0) == 20.0


def test_cart_total_matches_rounding_once_at_the_end():
    items = [41.95, 22.21, 38.35, 1.1]
    assert cart_total(items, 7.24) == 111.11


def test_cart_total_single_item_matches_price_with_tax():
    assert cart_total([50.0], 10) == price_with_tax(50.0, 10)


def test_cart_total_empty_cart():
    assert cart_total([], 10) == 0.0
