def price_with_tax(price: float, tax_pct: float) -> float:
    return round(price * (1 + tax_pct / 100), 2)


def cart_total(items: list[float], tax_pct: float) -> float:
    """items is a list of item prices, e.g. [19.99, 5.49, 3.50]."""
    subtotal = sum(items)
    total = price_with_tax(subtotal, tax_pct)
    return round(total, 2)
