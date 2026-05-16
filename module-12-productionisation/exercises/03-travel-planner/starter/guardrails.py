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
    """Check that daily spend in the itinerary is reasonable for the budget level.

    TODO:
    - Get the limit for the budget_level from BUDGET_LIMITS
    - Loop through itinerary days, check estimated_cost_usd against limit
    - Collect warnings for any day that exceeds the limit
    - Return dict with: valid (bool), budget_level, daily_limit_usd, warnings (list)
    """
    pass


def check_safety(destination: dict) -> dict:
    """Flag safety advisories for a destination.

    TODO:
    - Combine destination description and safety_notes into searchable text
    - Check each keyword in SAFETY_ADVISORIES against the text
    - Return dict with: destination name, safe (bool), advisories (list of flagged items)
    """
    pass
