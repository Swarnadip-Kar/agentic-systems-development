# Exercise 5 — Order Placement (partial-failure handling)

Implement `place_order(inventory, order, should_fail=False)` in
`starter.py`. Two helper functions already exist in the same file:

- `reserve_inventory(inventory, order)` — decrements `inventory` for each
  item in `order`. Raises `ValueError` if there isn't enough stock.
- `charge_payment(order, should_fail=False)` — charges the customer.
  Raises `PaymentError` if `should_fail` is `True` (this simulates a
  real payment gateway failure for testing purposes).

`place_order` should reserve inventory, then charge payment, and return
a confirmation dict: `{"status": "success", "order": order}` if it went
through, or `{"status": "failed", "order": order}` if the payment failed.

## Steps

1. Ask the assistant to implement `place_order` using both helpers.
2. Run the tests: `pytest exercises/05_order_placement/ -v`.
3. If a test fails, look at what state the `inventory` dict is actually
   in afterward, not just whether the function returned the right
   status. Ask the assistant to explain what happens to the reserved
   inventory when payment fails partway through — does its first answer
   actually account for that, or does it only handle the return value?
4. Once you understand the real gap, get it fixed.

## Write it up

In the root `NOTES.md`, record what the assistant's first implementation
did to `inventory` when payment failed, whether that matched what you'd
expect from a real order system, and what changed once you asked it to
account for that specifically.
