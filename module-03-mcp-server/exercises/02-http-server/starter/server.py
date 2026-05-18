"""
Exercise 02 — HTTP MCP Server: Science Lab
Build an HTTP FastMCP server with tools for the station's science lab.

Run:  python server.py   (starts at http://localhost:8000/mcp)
"""

import json

from mcp.server.fastmcp import FastMCP

server = FastMCP("Station Science Lab", stateless_http=True)

# ---------------------------------------------------------------------------
# Lab data
# ---------------------------------------------------------------------------

EXPERIMENTS = [
    {"id": "EXP-001", "title": "Crystal Growth in Zero-G", "status": "running", "lead": "Dr. Chen"},
    {"id": "EXP-002", "title": "Radiation Shielding Test", "status": "complete", "lead": "Lt. Sharma"},
    {"id": "EXP-003", "title": "Bacterial Colony Mapping", "status": "pending", "lead": "Ensign Morel"},
    {"id": "EXP-004", "title": "Alloy Stress Analysis", "status": "running", "lead": "Specialist Kwan"},
]

SAMPLES = {
    "S-101": {"type": "mineral", "origin": "Asteroid Belt", "mass_g": 42.5, "notes": "High iron content"},
    "S-102": {"type": "biological", "origin": "Titan", "mass_g": 0.3, "notes": "Frozen microorganism"},
    "S-103": {"type": "gas", "origin": "Jupiter Atmosphere", "mass_g": 1.2, "notes": "Methane-rich sample"},
    "S-104": {"type": "mineral", "origin": "Mars Surface", "mass_g": 88.0, "notes": "Regolith with water ice"},
}

ANALYSIS_METHODS = {
    "spectral": "Spectral analysis — identifies elemental composition via light absorption",
    "microscopy": "Electron microscopy — high-resolution structural imaging",
    "mass_spec": "Mass spectrometry — measures molecular weight and fragmentation patterns",
    "culture": "Culture growth — attempts to grow biological samples in controlled media",
}


# ---------------------------------------------------------------------------
# Tools — TODO: implement these
# ---------------------------------------------------------------------------


@server.tool()
def list_experiments(status: str | None = None) -> str:
    """List all experiments, optionally filtered by status (running/complete/pending)."""
    # TODO: Return all EXPERIMENTS as JSON
    # If status is provided, filter to only experiments with that status
    raise NotImplementedError


@server.tool()
def get_sample(sample_id: str) -> str:
    """Get details for a specific sample by ID."""
    # TODO: Look up sample_id in SAMPLES
    # Return the sample data as JSON (include the sample_id in the response)
    # If not found, return JSON with error message
    raise NotImplementedError


@server.tool()
def run_analysis(sample_id: str, method: str) -> str:
    """Run an analysis method on a sample. Returns analysis results."""
    # TODO: Validate sample_id exists in SAMPLES
    # Validate method exists in ANALYSIS_METHODS
    # Return JSON with sample_id, method, method description, and a result string
    # For the result, generate something based on the sample type and method
    # If sample or method not found, return JSON with error message
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Science Lab server starting at http://localhost:8000/mcp")
    server.run(transport="streamable-http")
