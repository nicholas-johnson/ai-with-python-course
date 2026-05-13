"""
Demo: Practical MCP tools — ship systems exposed as capabilities.
Run:  python module-03-mcp-server/demo/03_practical_tools.py

Exposes crew lookup, mission query, and sensor read tools.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

server = FastMCP("Pathfinder Ship Tools")

_crew = json.loads((DATA_DIR / "crew.json").read_text())
_missions = json.loads((DATA_DIR / "missions.json").read_text())
_logs = json.loads((DATA_DIR / "ship_logs.json").read_text())


@server.tool()
def query_crew(department: str | None = None) -> str:
    """Look up crew members, optionally filtering by department."""
    results = _crew
    if department:
        results = [m for m in results if m["department"] == department]
    return json.dumps([{"id": m["id"], "name": m["name"], "role": m["role"]} for m in results])


@server.tool()
def get_mission(mission_id: str) -> str:
    """Get details of a specific mission by ID."""
    for m in _missions:
        if m["id"] == mission_id:
            return json.dumps(m)
    return json.dumps({"error": f"Mission {mission_id} not found"})


@server.tool()
def search_logs(query: str, category: str | None = None, limit: int = 5) -> str:
    """Search ship logs by keyword, optionally filtering by category."""
    results = _logs
    if category:
        results = [log for log in results if log["category"] == category]
    results = [log for log in results if query.lower() in log["content"].lower()]
    return json.dumps(results[:limit])


if __name__ == "__main__":
    print("Starting MCP server with ship tools (stdio transport)...")
    print(f"Tools: query_crew, get_mission, search_logs")
    print(f"Data: {len(_crew)} crew, {len(_missions)} missions, {len(_logs)} logs")
    print("Press Ctrl+C to stop.\n")
    server.run()
