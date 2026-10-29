from starter import apply_coupon


def test_returns_new_cart_with_coupon_tag():
    cart = {"items": [{"name": "shirt", "tags": ["sale"]}], "total": 100}
    new_cart = apply_coupon(cart, "COUPON123")
    assert "COUPON123" in new_cart["items"][0]["tags"]


def test_does_not_mutate_original_cart():
    cart = {"items": [{"name": "shirt", "tags": ["sale"]}], "total": 100}
    apply_coupon(cart, "COUPON123")
    assert cart["items"][0]["tags"] == ["sale"]


def test_handles_empty_cart():
    cart = {"items": [], "total": 0}
    new_cart = apply_coupon(cart, "COUPON123")
    assert new_cart["items"] == []
