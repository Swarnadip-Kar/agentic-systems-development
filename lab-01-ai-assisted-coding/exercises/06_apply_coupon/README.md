# Exercise 6 — Apply Coupon (non-mutation)

Implement `apply_coupon(cart, coupon_code)` in `starter.py`. `cart` is a
dict shaped like:

```python
{"items": [{"name": "shirt", "tags": ["sale"]}, ...], "total": 100}
```

The function should return a **new** cart dict with `coupon_code`
appended to the first item's `tags` list — **without modifying the
original `cart` that was passed in.**

## Steps

1. Ask the assistant to implement this.
2. Run the tests: `pytest exercises/06_apply_coupon/ -v`.
3. If a test fails, don't just accept the assistant's explanation of
   *why* its code is correct — check it yourself. Print the original
   cart before and after calling `apply_coupon` in a scratch script. Did
   copying the item actually prevent the original from changing, in
   every field, or only some of them?
4. Once you understand the real cause, get it fixed.

## Write it up

In the root `NOTES.md`, record what the assistant's first explanation
claimed about copying the cart, and whether that explanation actually
held up once you checked it yourself.
