"""Safety guardrails for travel planning."""

BUDGET_LIMITS = {
    "budget": 150,
    "moderate": 400,
    "luxury": 1200,
}

SAFETY_ADVISORIES = {
    "conflict_zones": ["active conflict", "war zone", "military operation"],
    "health_risks": ["disease outbreak", "epidemic", "quarantine"],
    "natural_disasters": ["hurricane warning", "earthquake zone", "volcanic activity"],
}


def validate_budget(itinerary: list[dict], budget_level: str) -> dict:
    """Check that daily spend in the itinerary is reasonable for the budget level."""
    limit = BUDGET_LIMITS.get(budget_level, BUDGET_LIMITS["moderate"])
    warnings = []
    for day in itinerary:
        cost = day.get("estimated_cost_usd", 0)
        if cost > limit:
            warnings.append(
                f"Day {day.get('day', '?')}: ${cost} exceeds {budget_level} limit of ${limit}"
            )
    return {
        "valid": len(warnings) == 0,
        "budget_level": budget_level,
        "daily_limit_usd": limit,
        "warnings": warnings,
    }


def check_safety(destination: dict) -> dict:
    """Flag safety advisories for a destination."""
    description = destination.get("description", "").lower()
    notes = destination.get("safety_notes", "").lower()
    text = f"{description} {notes}"

    flags = []
    for category, keywords in SAFETY_ADVISORIES.items():
        for keyword in keywords:
            if keyword in text:
                flags.append({"category": category, "keyword": keyword})

    return {
        "destination": destination.get("name", "Unknown"),
        "safe": len(flags) == 0,
        "advisories": flags,
    }
