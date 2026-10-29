"""Q1: extract a dollar amount from free text.

Aider: NOT ALLOWED for this question. Using Aider, or any AI
code-generation assistant, to write your solution here means this
question will not be evaluated.
"""


def parse_price(text):
    """Return the first dollar amount in `text` as a float.

    Raise ValueError if no dollar amount is present.
    Scope: amounts are non-negative, with at most two decimal digits,
    optionally comma-grouped (e.g. $1,234.56). Negative amounts and
    other formats are out of scope.
    Examples:
      parse_price("The total comes to $42.50 for your order.") -> 42.5
      parse_price("That will be $9 today.") -> 9.0
      parse_price("Total: $1,234.56 due") -> 1234.56
      parse_price("no price mentioned here at all") -> raises ValueError
    """

    # Strip leading and trailing whitespace
    s = text.strip()
    
    # Check if the string is empty after stripping
    if not s:
        raise ValueError("Input string is empty or contains only whitespace.")
    
    if '$' not in s:
        raise ValueError("Input string has no dollar signs.")
    
    
    while not s.startswith('$'):
        s = s[1:].strip()

    # Remove the dollar sign
    if s.startswith('$'):
        s = s[1:].strip()
    
    # remove the end
    pos = text.find(' ')
    if (pos != -1):
      s=s[:pos+2]


    # Remove commas (thousand separators)
    s = s.replace(',', '')
    
    # Try to convert the cleaned string to a float
    try:
        price = float(s)
    except ValueError:
        raise ValueError(f"Invalid price string: '{s}'. The string should represent a valid number.")
    
    return price

