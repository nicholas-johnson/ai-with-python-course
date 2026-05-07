"""
Exercise 02 — Ship Tools (solution)
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

server = FastMCP("Pathfinder Ship Tools")

_crew = json.loads((DATA_DIR / "crew.json").read_text())
_logs = json.loads((DATA_DIR / "ship_logs.json").read_text())


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
def query_crew(department: str | None = None) -> str:
    """Look up crew members, optionally filtering by department."""
    results = _crew
    if department:
        results = [m for m in results if m["department"] == department]
    return json.dumps([{"id": m["id"], "name": m["name"], "role": m["role"]} for m in results])


@server.tool()
def search_logs(query: str, category: str | None = None, limit: int = 5) -> str:
    """Search ship logs by keyword, optionally filtering by category."""
    results = _logs
    if category:
        results = [log for log in results if log["category"] == category]
    results = [log for log in results if query.lower() in log["content"].lower()]
    return json.dumps(results[:limit])
