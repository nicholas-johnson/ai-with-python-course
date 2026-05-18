"""
Module 3 Demo — Navigation MCP Server (Streamable HTTP)
Runs at http://localhost:8000/mcp

Start:  python http_server.py
"""

import json
import math

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Navigation", stateless_http=True)

# ---------------------------------------------------------------------------
# Navigation data
# ---------------------------------------------------------------------------

LOCATIONS = {
    "earth": {"name": "Earth", "sector": "Sol-A", "x": 0.0, "y": 0.0},
    "mars": {"name": "Mars", "sector": "Sol-A", "x": 1.5, "y": 0.3},
    "titan": {"name": "Titan Station", "sector": "Sol-B", "x": 9.5, "y": 2.1},
    "proxima": {"name": "Proxima Centauri", "sector": "Alpha-1", "x": 42.0, "y": 12.0},
    "kepler": {"name": "Kepler-442b", "sector": "Lyra-7", "x": 130.0, "y": 45.0},
    "vega": {"name": "Vega Outpost", "sector": "Lyra-2", "x": 125.0, "y": 50.0},
    "andoria": {"name": "Andoria Prime", "sector": "Theta-9", "x": 200.0, "y": 80.0},
}

SPACE_OBJECTS = [
    {"name": "Sol", "type": "star", "sector": "Sol-A", "x": 0.0, "y": 0.0},
    {"name": "Jupiter", "type": "gas_giant", "sector": "Sol-A", "x": 5.2, "y": 0.8},
    {"name": "Oort Cloud", "type": "anomaly", "sector": "Sol-B", "x": 10.0, "y": 3.0},
    {"name": "Alpha Centauri A", "type": "star", "sector": "Alpha-1", "x": 40.0, "y": 11.0},
    {"name": "Relay Station 7", "type": "station", "sector": "Alpha-1", "x": 43.0, "y": 13.0},
    {"name": "Lyra Nebula", "type": "anomaly", "sector": "Lyra-7", "x": 128.0, "y": 46.0},
    {"name": "Vega Drydock", "type": "station", "sector": "Lyra-2", "x": 126.0, "y": 51.0},
    {"name": "Theta Rift", "type": "anomaly", "sector": "Theta-9", "x": 198.0, "y": 78.0},
]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool()
def plot_course(origin: str, destination: str) -> str:
    """Plot a course between two known locations. Returns heading, distance, and ETA."""
    o = LOCATIONS.get(origin.lower())
    d = LOCATIONS.get(destination.lower())
    if not o:
        return json.dumps({"error": f"Unknown origin: {origin}"})
    if not d:
        return json.dumps({"error": f"Unknown destination: {destination}"})

    dx, dy = d["x"] - o["x"], d["y"] - o["y"]
    distance = math.sqrt(dx**2 + dy**2)
    heading = round(math.degrees(math.atan2(dy, dx)) % 360, 1)
    eta_hours = round(distance / 5.0, 1)

    return json.dumps({
        "origin": o["name"],
        "destination": d["name"],
        "heading": heading,
        "distance_ly": round(distance, 2),
        "eta_hours": eta_hours,
    })


@server.tool()
def get_coordinates(location: str) -> str:
    """Get the sector and coordinates for a named location."""
    loc = LOCATIONS.get(location.lower())
    if not loc:
        known = ", ".join(LOCATIONS.keys())
        return json.dumps({"error": f"Unknown location: {location}", "known": known})
    return json.dumps(loc)


@server.tool()
def nearby_objects(sector: str, radius: float) -> str:
    """Find objects (stars, stations, anomalies) near a sector within a given radius."""
    sector_locs = [l for l in LOCATIONS.values() if l["sector"] == sector]
    if not sector_locs:
        return json.dumps({"error": f"Unknown sector: {sector}"})

    cx = sum(l["x"] for l in sector_locs) / len(sector_locs)
    cy = sum(l["y"] for l in sector_locs) / len(sector_locs)

    matches = []
    for obj in SPACE_OBJECTS:
        dist = math.sqrt((obj["x"] - cx) ** 2 + (obj["y"] - cy) ** 2)
        if dist <= radius:
            matches.append({**obj, "distance_ly": round(dist, 2)})

    matches.sort(key=lambda o: o["distance_ly"])
    return json.dumps(matches)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Pathfinder Navigation server starting at http://localhost:8000/mcp")
    server.run(transport="streamable-http")
