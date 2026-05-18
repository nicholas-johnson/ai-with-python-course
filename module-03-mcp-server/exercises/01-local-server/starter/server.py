"""
Exercise 01 — Local MCP Server: Power Grid
Build a stdio FastMCP server with tools for managing the station's power grid.
"""

import json

from mcp.server.fastmcp import FastMCP

server = FastMCP("Station Power Grid")

# ---------------------------------------------------------------------------
# Power grid data
# ---------------------------------------------------------------------------

POWER_GRID = {
    "habitat": {"power_level": 850, "capacity": 1000, "load": 720, "status": "online"},
    "lab": {"power_level": 600, "capacity": 800, "load": 580, "status": "online"},
    "docking": {"power_level": 300, "capacity": 500, "load": 150, "status": "standby"},
    "comms": {"power_level": 400, "capacity": 400, "load": 390, "status": "warning"},
}

ALERTS = [
    {"module": "comms", "severity": "warning", "message": "Power load at 97% capacity"},
    {"module": "lab", "severity": "info", "message": "Scheduled maintenance in 2 hours"},
]


# ---------------------------------------------------------------------------
# Tools — TODO: implement these
# ---------------------------------------------------------------------------


@server.tool()
def get_power_status(module: str) -> str:
    """Get power level, load, and status for a station module."""
    # TODO: Look up the module in POWER_GRID
    # Return JSON with module name, power_level, capacity, load, status
    # If module not found, return JSON with error message
    raise NotImplementedError


@server.tool()
def allocate_power(source: str, target: str, amount: int) -> str:
    """Transfer power between two station modules."""
    # TODO: Validate both modules exist in POWER_GRID
    # Check source has enough power (power_level >= amount)
    # Check target won't exceed capacity (power_level + amount <= capacity)
    # If valid: subtract from source, add to target, return success JSON
    # If invalid: return JSON with error message
    raise NotImplementedError


@server.tool()
def list_alerts() -> str:
    """List all current power grid alerts."""
    # TODO: Return the ALERTS list as JSON
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
