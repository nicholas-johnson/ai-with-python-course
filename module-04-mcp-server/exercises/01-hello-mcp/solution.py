"""
Exercise 01 — Hello MCP (solution)
"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("Hello Pathfinder")


@server.tool()
def greet(name: str = "Engineer") -> str:
    """Greet a crew member boarding the DSS Pathfinder."""
    return f"Welcome aboard, {name}. The DSS Pathfinder awaits."


@server.tool()
def ship_time() -> str:
    """Return the current shipboard time."""
    return "Stardate 2347.078 — 0800 hours shipboard time."
