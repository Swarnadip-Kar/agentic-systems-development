def apply_coupon(cart: dict, coupon_code: str) -> dict:
    # Debug statement to print the original cart
    print(f"Original cart: {cart}")
    
    # Create a deep copy of the cart to avoid modifying the original
    new_cart = {
        "items": [{**item, "tags": item["tags"][:]} for item in cart["items"]],
        "total": cart["total"]
    }
    
    # Debug statement to print the new cart after copying
    print(f"New cart after copying: {new_cart}")
    
    # Append the coupon code to the first item's tags list if there are items
    if new_cart["items"]:
        new_cart["items"][0]["tags"].append(coupon_code)
    
    # Debug statement to print the new cart after appending the coupon code
    print(f"New cart after appending coupon code: {new_cart}")
    
    return new_cart
