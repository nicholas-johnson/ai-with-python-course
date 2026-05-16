"""Tool implementations for the travel planning agent."""

import random


WEATHER_DATA = {
    "sunny": {"temp_c": 28, "condition": "Sunny", "humidity": 40},
    "mild": {"temp_c": 22, "condition": "Partly cloudy", "humidity": 55},
    "rainy": {"temp_c": 18, "condition": "Light rain", "humidity": 75},
    "cold": {"temp_c": 8, "condition": "Overcast", "humidity": 60},
    "hot": {"temp_c": 35, "condition": "Hot and dry", "humidity": 25},
}

BUDGET_RATES = {
    "budget": {"accommodation": 40, "food": 25, "activities": 20, "transport": 15},
    "moderate": {"accommodation": 120, "food": 60, "activities": 50, "transport": 30},
    "luxury": {"accommodation": 350, "food": 150, "activities": 120, "transport": 80},
}


def get_weather(city: str) -> dict:
    """Return mock weather data for a city."""
    seed = sum(ord(c) for c in city.lower())
    random.seed(seed)
    pattern = random.choice(list(WEATHER_DATA.keys()))
    data = WEATHER_DATA[pattern].copy()
    data["city"] = city
    data["temp_c"] += random.randint(-3, 3)
    data["forecast"] = [
        random.choice(["Sunny", "Partly cloudy", "Light rain", "Clear"])
        for _ in range(5)
    ]
    return data


def estimate_budget(activities: list[str], budget_level: str) -> dict:
    """Estimate daily costs based on activities and budget level."""
    rates = BUDGET_RATES.get(budget_level, BUDGET_RATES["moderate"])
    activity_cost = rates["activities"] * len(activities) * 0.6
    daily_total = rates["accommodation"] + rates["food"] + activity_cost + rates["transport"]
    return {
        "budget_level": budget_level,
        "daily_estimate_usd": round(daily_total, 2),
        "breakdown": {
            "accommodation": rates["accommodation"],
            "food": rates["food"],
            "activities": round(activity_cost, 2),
            "transport": rates["transport"],
        },
        "num_activities": len(activities),
    }


def estimate_travel_time(from_loc: str, to_loc: str) -> dict:
    """Return mock travel time between two locations."""
    seed = sum(ord(c) for c in (from_loc + to_loc).lower())
    random.seed(seed)
    minutes = random.randint(10, 90)
    return {
        "from": from_loc,
        "to": to_loc,
        "duration_minutes": minutes,
        "mode": "taxi" if minutes < 20 else "public transport",
    }
