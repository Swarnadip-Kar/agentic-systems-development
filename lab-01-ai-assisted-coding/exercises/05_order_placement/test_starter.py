import pytest
from starter import place_order


def test_successful_order_decrements_inventory():
    inventory = {"widget": 10}
    order = {"widget": 3}
    result = place_order(inventory, order, should_fail=False)
    assert inventory["widget"] == 7
    assert result["status"] == "success"


def test_failed_payment_rolls_back_inventory():
    inventory = {"widget": 10}
    order = {"widget": 3}
    result = place_order(inventory, order, should_fail=True)
    assert inventory["widget"] == 10
    assert result["status"] == "failed"


def test_insufficient_inventory_raises_before_charging():
    inventory = {"widget": 1}
    order = {"widget": 3}
    with pytest.raises(ValueError):
        place_order(inventory, order, should_fail=False)
    assert inventory["widget"] == 1
