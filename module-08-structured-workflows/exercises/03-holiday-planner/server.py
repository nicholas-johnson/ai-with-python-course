"""
Exercise 03 — Holiday Planner MCP Server (scaffold)
=====================================================
A FastMCP server with holiday planning tools.

Run standalone:  python server.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Holiday Planner")

_preferences: dict[str, str] = {}


# TODO: Implement search_web tool
# @mcp.tool()
# def search_web(query: str) -> str:
#     """Search the web for travel information."""
#     Use httpx to GET https://lite.duckduckgo.com/lite?q={query}
#     Parse text from HTML, return snippet
#     Fall back to mock results on failure


# TODO: Implement remember_preference tool
# @mcp.tool()
# def remember_preference(key: str, value: str) -> str:
#     """Store a user travel preference (e.g. budget, dietary needs, interests)."""
#     Store in _preferences dict
#     Return confirmation


# TODO: Implement recall_preferences tool
# @mcp.tool()
# def recall_preferences() -> str:
#     """Recall all stored user travel preferences."""
#     Return formatted preferences or "No preferences stored yet."


# TODO: Implement search_flights tool
# @mcp.tool()
# def search_flights(origin: str, destination: str, date: str) -> str:
#     """Search for flights between two cities on a given date."""
#     Return mock flight results with airline, price, duration, stops


# TODO: Implement search_hotels tool
# @mcp.tool()
# def search_hotels(location: str, checkin: str, checkout: str) -> str:
#     """Search for hotels in a location for given dates."""
#     Return mock hotel results with name, stars, price, amenities


if __name__ == "__main__":
    mcp.run()
