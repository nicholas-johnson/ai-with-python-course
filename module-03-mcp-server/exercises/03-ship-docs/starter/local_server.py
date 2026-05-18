"""
Exercise 01 — Local MCP Server: Power Grid (solution)
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
# Tools
# ---------------------------------------------------------------------------


@server.tool()
def get_power_status(module: str) -> str:
    """Get power level, load, and status for a station module."""
    info = POWER_GRID.get(module)
    if not info:
        return json.dumps({"error": f"Unknown module: {module}"})
    return json.dumps({"module": module, **info})


@server.tool()
def allocate_power(source: str, target: str, amount: int) -> str:
    """Transfer power between two station modules."""
    if source not in POWER_GRID:
        return json.dumps({"error": f"Unknown source module: {source}"})
    if target not in POWER_GRID:
        return json.dumps({"error": f"Unknown target module: {target}"})

    src = POWER_GRID[source]
    tgt = POWER_GRID[target]

    if src["power_level"] < amount:
        return json.dumps({"error": f"{source} has insufficient power ({src['power_level']} < {amount})"})
    if tgt["power_level"] + amount > tgt["capacity"]:
        return json.dumps({"error": f"{target} would exceed capacity ({tgt['power_level']} + {amount} > {tgt['capacity']})"})

    src["power_level"] -= amount
    tgt["power_level"] += amount
    return json.dumps({
        "success": True,
        "transferred": amount,
        "source": {"module": source, "power_level": src["power_level"]},
        "target": {"module": target, "power_level": tgt["power_level"]},
    })


@server.tool()
def list_alerts() -> str:
    """List all current power grid alerts."""
    return json.dumps(ALERTS)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
