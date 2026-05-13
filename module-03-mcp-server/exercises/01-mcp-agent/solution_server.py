"""
Exercise 01 — MCP Server (solution)
"""

import json

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Ship")

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


@server.tool()
def get_crew_count(department: str) -> str:
    """Get the number of crew members in a department."""
    crew = CREW_DATA.get(department, [])
    return json.dumps({"department": department, "count": len(crew)})


@server.tool()
def get_ship_status(system: str) -> str:
    """Get the current status of a ship system."""
    status = SHIP_SYSTEMS.get(system, {"system": system, "status": "unknown"})
    return json.dumps(status)


@server.tool()
def search_crew(query: str) -> str:
    """Search crew members by name or role."""
    matches = []
    q = query.lower()
    for dept, members in CREW_DATA.items():
        for member in members:
            if q in member["name"].lower() or q in member["role"].lower():
                matches.append({**member, "department": dept})
    return json.dumps(matches)


if __name__ == "__main__":
    server.run()
