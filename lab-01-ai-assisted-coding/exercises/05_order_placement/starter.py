class PaymentError(Exception):
    pass


def reserve_inventory(inventory: dict, order: dict) -> None:
    for product_id, qty in order.items():
        if inventory.get(product_id, 0) < qty:
            raise ValueError(f"not enough inventory for {product_id}")
        inventory[product_id] -= qty


def charge_payment(order: dict, should_fail: bool = False) -> None:
    if should_fail:
        raise PaymentError("payment failed")


def place_order(inventory: dict, order: dict, should_fail: bool = False) -> dict:
    try:
        # Reserve inventory
        reserve_inventory(inventory, order)
        
        # Charge payment
        charge_payment(order, should_fail)
        
        return {"status": "success", "order": order}
    except ValueError as ve:
        # Restore inventory if there was insufficient inventory
        for product_id, qty in order.items():
            if product_id in inventory:
                inventory[product_id] += qty
        raise ve  # Re-raise the ValueError to ensure it is caught by the test
    except PaymentError as pe:
        # Restore inventory if payment fails
        for product_id, qty in order.items():
            if product_id in inventory:
                inventory[product_id] += qty
        return {"status": "failed", "order": order, "error": str(pe)}
