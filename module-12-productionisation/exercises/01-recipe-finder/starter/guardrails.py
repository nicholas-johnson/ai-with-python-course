"""Safety guardrails — allergen checking and PII redaction."""

import re

COMMON_ALLERGENS = [
    "peanut", "tree nut", "almond", "cashew", "walnut", "pecan",
    "milk", "dairy", "cream", "cheese", "butter",
    "egg",
    "wheat", "gluten", "flour",
    "soy", "soybean",
    "fish", "salmon", "tuna", "cod",
    "shellfish", "shrimp", "crab", "lobster",
    "sesame",
]


def check_allergens(recipe: dict, user_restrictions: list[str]) -> list[str]:
    """Return list of allergens found in the recipe that match user restrictions.

    Steps:
    1. If user_restrictions is empty, return []
    2. Combine recipe title, ingredients, and description into one lowercase string
    3. For each restriction, check if it appears in the text directly
    4. Also check against COMMON_ALLERGENS for related matches
    5. Return list of matched restrictions
    """
    # TODO: implement allergen checking
    return []


def redact_pii(text: str) -> str:
    """Redact emails and phone numbers from text.

    Steps:
    1. Use regex to replace email addresses with "[EMAIL REDACTED]"
    2. Use regex to replace phone numbers (e.g. 123-456-7890) with "[PHONE REDACTED]"
    3. Return the cleaned text
    """
    # TODO: implement PII redaction
    return text
