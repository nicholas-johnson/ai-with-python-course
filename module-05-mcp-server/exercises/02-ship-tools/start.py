"""
Exercise 02 — Ship Tools
Build an MCP server with three ship-system tools.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

server = FastMCP("Pathfinder Ship Tools")

_crew = json.loads((DATA_DIR / "crew.json").read_text())
_logs = json.loads((DATA_DIR / "ship_logs.json").read_text())


# TODO: Register a 'read_sensor' tool
# - Takes sensor_id (str)
# - Returns JSON string with sensor_id, value (float), unit, and status
# - Simulate the value based on the sensor_id hash (so it's deterministic)


# TODO: Register a 'query_crew' tool
# - Takes department (str, optional)
# - Returns JSON string: list of {id, name, role} for matching crew


# TODO: Register a 'search_logs' tool
# - Takes query (str), category (str, optional), limit (int, default 5)
# - Returns JSON string: matching log entries (search content field)
