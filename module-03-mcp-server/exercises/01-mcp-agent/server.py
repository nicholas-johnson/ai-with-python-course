"""
Exercise 01 — MCP Server
Build a FastMCP server with ship tools.

Run directly:  python server.py   (starts MCP stdio server)
Used by:       start.py connects to this server automatically.
"""

import json

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Ship")

# ---------------------------------------------------------------------------
# Ship data (hardcoded for simplicity)
# ---------------------------------------------------------------------------

CREW_DATA = {
    "command": [{"name": "Commander Elara Voss", "role": "Captain"}],
    "science": [
        {"name": "Dr. Jian Chen", "role": "Chief Science Officer"},
        {"name": "Ensign Dax Morel", "role": "Xenobiologist"},
        {"name": "Lt. Priya Sharma", "role": "Astrophysicist"},
    ],
    "engineering": [
        {"name": "Chief Engineer Mira Chen", "role": "Lead Engineer"},
        {"name": "Specialist Bodhi Kwan", "role": "Systems Tech"},
    ],
    "medical": [{"name": "Dr. Amara Osei", "role": "Chief Medical Officer"}],
}

SHIP_SYSTEMS = {
    "warp": {"system": "warp", "status": "online", "efficiency": 0.97},
    "shields": {"system": "shields", "status": "online", "efficiency": 0.85},
    "sensors": {"system": "sensors", "status": "degraded", "efficiency": 0.62},
    "life_support": {"system": "life_support", "status": "online", "efficiency": 0.99},
}


# ---------------------------------------------------------------------------
# TODO: Register three tools using @server.tool()
# ---------------------------------------------------------------------------

# TODO: get_crew_count(department: str) -> str
#   Return JSON with department name and crew count.
#   If department not found, return count 0.


# TODO: get_ship_status(system: str) -> str
#   Return JSON with system name, status, and efficiency.
#   If system not found, return {"system": system, "status": "unknown"}.


# TODO: search_crew(query: str) -> str
#   Search all departments for crew matching query (case-insensitive).
#   Match against name or role. Return JSON list of matches with department.


# ---------------------------------------------------------------------------
# Run as MCP server (stdio transport)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
