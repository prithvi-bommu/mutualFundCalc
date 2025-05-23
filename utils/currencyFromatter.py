def format_in_indian_style(n):
    s = str(int(n))
    # First group (last 3 digits)
    if len(s) <= 3:
        return s
    else:
        # Split into last 3 digits and rest
        last3 = s[-3:]
        rest = s[:-3]
        # Group rest in twos
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        return ','.join(parts + [last3])

def format_inr(n):
    return f"₹{format_in_indian_style(n)}"
