"""
Exercise 02 — Data Tools Server (solution)
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Data Tools")

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

_crew = json.loads((DATA_DIR / "crew.json").read_text())
_logs = json.loads((DATA_DIR / "ship_logs.json").read_text())
_missions = json.loads((DATA_DIR / "missions.json").read_text())


@server.tool()
def query_crew(department: str | None = None, role: str | None = None) -> str:
    """Look up crew members, optionally filtering by department and role."""
    results = _crew
    if department:
        results = [m for m in results if m.get("department", "").lower() == department.lower()]
    if role:
        results = [m for m in results if role.lower() in m.get("role", "").lower()]
    return json.dumps([
        {"id": m.get("id", ""), "name": m["name"], "role": m["role"], "department": m.get("department", "")}
        for m in results
    ])


@server.tool()
def search_logs(keyword: str, category: str | None = None, limit: int = 5) -> str:
    """Search ship logs by keyword, optionally filtering by category."""
    results = _logs
    if category:
        results = [log for log in results if log.get("category", "").lower() == category.lower()]
    results = [log for log in results if keyword.lower() in log.get("content", "").lower()]
    return json.dumps(results[:limit])


@server.tool()
def read_sensor(sensor_id: str) -> str:
    """Read the latest value from a ship sensor by ID."""
    value = (hash(sensor_id) % 1000) / 10.0
    return json.dumps({
        "sensor_id": sensor_id,
        "value": value,
        "unit": "celsius",
        "status": "nominal" if value < 80 else "warning",
    })


@server.tool()
def list_missions() -> str:
    """List all known missions."""
    return json.dumps(_missions)


if __name__ == "__main__":
    server.run()
