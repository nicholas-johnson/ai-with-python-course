"""
Exercise 02 — Data Tools Server
MCP server reading from the course JSON data files.

Run directly:  python server.py
Used by:       start.py connects to this server automatically.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Data Tools")

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

_crew = json.loads((DATA_DIR / "crew.json").read_text())
_logs = json.loads((DATA_DIR / "ship_logs.json").read_text())
_missions = json.loads((DATA_DIR / "missions.json").read_text())


# ---------------------------------------------------------------------------
# TODO: Register four tools using @server.tool()
# ---------------------------------------------------------------------------

# TODO: query_crew(department: str | None = None, role: str | None = None) -> str
#   Filter _crew by department and/or role (case-insensitive substring match).
#   Return JSON list of {id, name, role, department} for matching crew.


# TODO: search_logs(keyword: str, category: str | None = None, limit: int = 5) -> str
#   Search _logs for entries where keyword appears in the "content" field.
#   Optionally filter by category. Return up to `limit` results as JSON.


# TODO: read_sensor(sensor_id: str) -> str
#   Simulate a sensor reading. Use hash(sensor_id) % 1000 / 10.0 for the value.
#   Return JSON with sensor_id, value, unit ("celsius"), and status
#   ("nominal" if value < 80, else "warning").


# TODO: list_missions() -> str
#   Return _missions as a JSON string.


# ---------------------------------------------------------------------------
# Run as MCP server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
