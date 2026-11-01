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
    """Return mock weather data for a city.

    TODO:
    - Use the city name as a seed for deterministic random output
    - Return dict with: city, temp_c, condition, humidity, forecast (5-day list)
    """
    pass


def estimate_budget(activities: list[str], budget_level: str) -> dict:
    """Estimate daily costs based on activities and budget level.

    TODO:
    - Look up rates from BUDGET_RATES (default to "moderate")
    - Calculate activity_cost = rates["activities"] * len(activities) * 0.6
    - Sum up daily_total from accommodation + food + activity_cost + transport
    - Return dict with: budget_level, daily_estimate_usd, breakdown, num_activities
    """
    pass


def estimate_travel_time(from_loc: str, to_loc: str) -> dict:
    """Return mock travel time between two locations.

    TODO:
    - Use combined location names as seed for deterministic random
    - Generate random minutes (10-90)
    - Return dict with: from, to, duration_minutes, mode (taxi if <20 min, else public transport)
    """
    pass
