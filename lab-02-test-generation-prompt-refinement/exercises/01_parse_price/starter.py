def parse_price(s: str) -> float:
    # Strip leading and trailing whitespace
    s = s.strip()
    
    # Check if the string is empty after stripping
    if not s:
        raise ValueError("Input string is empty or contains only whitespace.")
    
    # Handle negative sign
    negative = False
    if s.startswith('-'):
        negative = True
        s = s[1:].strip()
    
    # Remove the dollar sign if present
    if s.startswith('$'):
        s = s[1:].strip()
    
    # Check for multiple dollar signs
    if '$' in s:
        raise ValueError("Input string contains multiple dollar signs.")
    
    # Remove commas (thousand separators)
    s = s.replace(',', '')
    
    # Try to convert the cleaned string to a float
    try:
        price = float(s)
    except ValueError:
        raise ValueError(f"Invalid price string: '{s}'. The string should represent a valid number.")
    
    if negative:
        price = -price
    
    return price
