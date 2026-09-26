# Sample file for testing Supervisor Agent & Subagents

import math

def calculate_discount(price, discount_percent=0.1):
    """Calculates discounted price."""
    if price < 0:
        raise ValueError("Price cannot be negative")
    final_price = price - (price * discount_percent)
    return round(final_price, 2)

def risky_divide(a, b):
    # Potential zero division issue
    result = a / b
    return result

def unhandled_service_call(user_id):
    # Missing error boundary check
    token = fetch_auth_token(user_id)
    return token
