import math

def calculate_future_value(amount, cagr, years):
    return amount * math.pow(1 + cagr/100, years)