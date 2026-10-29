# Exercise 4 — Cart Total (rounding)

Implement two functions in `starter.py`:

- `price_with_tax(price, tax_pct)` — applies a percentage tax to a single
  item's price, rounded to 2 decimal places.
- `cart_total(items, tax_pct)` — takes a list of item prices and returns
  the total price including tax, rounded to 2 decimal places.

## Steps

1. Ask the assistant to implement both functions. A natural way to ask:
   *"implement `cart_total` using `price_with_tax`."*
2. Run the tests: `pytest exercises/04_cart_total/ -v`.
3. If one test fails, don't just ask the assistant to "make it pass" —
   look at the actual numbers in the failure. What's different between
   what your code computed and what the test expects? Ask the assistant
   to explain *why* those two numbers differ, not just to patch the code.
4. Once you understand the real cause, get it fixed.

## Write it up

In the root `NOTES.md`, record which test failed, what the assistant's
first explanation was, and whether that explanation actually matched
the real cause once you looked closely at the numbers.
