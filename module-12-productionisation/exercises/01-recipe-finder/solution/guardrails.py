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
    """Return list of allergens found in the recipe that match user restrictions."""
    if not user_restrictions:
        return []

    text = " ".join([
        recipe.get("title", ""),
        " ".join(recipe.get("ingredients", [])),
        recipe.get("description", ""),
    ]).lower()

    flagged = []
    for restriction in user_restrictions:
        restriction_lower = restriction.lower().strip()
        if restriction_lower in text:
            flagged.append(restriction)
        for allergen in COMMON_ALLERGENS:
            if restriction_lower in allergen or allergen in restriction_lower:
                if allergen in text and restriction not in flagged:
                    flagged.append(restriction)
    return flagged


def redact_pii(text: str) -> str:
    """Redact emails and phone numbers from text."""
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL REDACTED]", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE REDACTED]", text)
    return text
