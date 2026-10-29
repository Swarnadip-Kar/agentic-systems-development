import math

def batch_pack_quantities(order_qty: int, pack_size: int) -> int:
    """
    Given the order quantity and pack size, returns the number of packs needed to cover the order.
    
    Assumptions:
    - order_qty and pack_size are non-negative integers.
    - pack_size is greater than zero.
    
    Edge Cases:
    - If order_qty is zero, return 0.
    - If pack_size is zero, raise a ValueError.
    """
    if not isinstance(order_qty, int) or not isinstance(pack_size, int):
        raise TypeError("Both order quantity and pack size must be integers.")
    if order_qty < 0:
        raise ValueError("Order quantity cannot be negative.")
    if pack_size <= 0:
        raise ValueError("Pack size must be greater than zero.")
    
    # Calculate the number of full packs needed, rounding up if there's a remainder
    return math.ceil(order_qty / pack_size)
