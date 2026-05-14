"""
Exercise 03 — Holiday Planner MCP Server (Solution)
=====================================================
A FastMCP server with holiday planning tools.

Run standalone:  python solution_server.py
"""
from __future__ import annotations
import json
import random
import re

from mcp.server.fastmcp import FastMCP

try:
    import httpx
except ImportError:
    httpx = None

mcp = FastMCP("Holiday Planner")

_preferences: dict[str, str] = {}


@mcp.tool()
def search_web(query: str) -> str:
    """Search the web for travel information. Returns a text summary."""
    if httpx is not None:
        try:
            resp = httpx.get(
                "https://lite.duckduckgo.com/lite",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                follow_redirects=True,
            )
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            snippet = text[:1500]
            if snippet:
                return f"Search results for '{query}':\n{snippet}"
        except Exception:
            pass

    return (
        f"Search results for '{query}': "
        f"[mock] Here are some relevant travel facts about {query}. "
        f"This is a simulated search result for demonstration purposes."
    )


@mcp.tool()
def remember_preference(key: str, value: str) -> str:
    """Store a user travel preference (e.g. budget, dietary needs, interests)."""
    _preferences[key] = value
    return f"Preference saved: {key} = {value} ({len(_preferences)} total preferences)"


@mcp.tool()
def recall_preferences() -> str:
    """Recall all stored user travel preferences."""
    if not _preferences:
        return "No preferences stored yet."
    lines = [f"  {k}: {v}" for k, v in _preferences.items()]
    return "User preferences:\n" + "\n".join(lines)


@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights between two cities on a given date. Returns available options."""
    airlines = [
        ("SkyWay Airlines", "SW"),
        ("Pacific Air", "PA"),
        ("Global Express", "GX"),
        ("Horizon Flights", "HF"),
        ("Atlas Airways", "AA"),
    ]

    results = []
    for airline_name, code in random.sample(airlines, min(3, len(airlines))):
        flight_num = f"{code}{random.randint(100, 999)}"
        price = random.randint(250, 1200)
        hours = random.randint(2, 18)
        mins = random.choice([0, 15, 30, 45])
        stops = random.choice([0, 0, 1, 1, 2])
        dep_hour = random.randint(6, 22)
        dep_min = random.choice(["00", "15", "30", "45"])

        stop_text = "direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
        results.append(
            f"  {flight_num} | {airline_name} | {origin} → {destination} | "
            f"{date} {dep_hour}:{dep_min} | {hours}h{mins:02d}m | {stop_text} | ${price}"
        )

    header = f"Flights from {origin} to {destination} on {date}:\n"
    return header + "\n".join(results)


@mcp.tool()
def search_hotels(location: str, checkin: str, checkout: str) -> str:
    """Search for hotels in a location for given dates. Returns available options."""
    hotels = [
        ("Grand Plaza Hotel", 5, ["pool", "spa", "gym", "restaurant", "concierge"]),
        ("City Center Inn", 3, ["wifi", "breakfast", "parking"]),
        ("Sunset Boutique Hotel", 4, ["pool", "restaurant", "bar", "wifi"]),
        ("Budget Stay Express", 2, ["wifi", "parking"]),
        ("The Royal Residence", 5, ["pool", "spa", "gym", "restaurant", "rooftop bar"]),
        ("Harbor View Suites", 4, ["ocean view", "restaurant", "gym", "wifi"]),
        ("Backpacker's Lodge", 1, ["wifi", "shared kitchen", "lockers"]),
    ]

    results = []
    for name, stars, amenities in random.sample(hotels, min(4, len(hotels))):
        base_price = stars * random.randint(30, 80)
        star_str = "\u2b50" * stars
        amenity_str = ", ".join(amenities[:4])
        results.append(
            f"  {name} | {star_str} | ${base_price}/night | "
            f"Amenities: {amenity_str}"
        )

    header = f"Hotels in {location} ({checkin} to {checkout}):\n"
    return header + "\n".join(results)


if __name__ == "__main__":
    mcp.run()
