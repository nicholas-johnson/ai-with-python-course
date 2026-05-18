"""
Exercise 02 — HTTP MCP Server: Science Lab (solution)
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

ANALYSIS_RESULTS = {
    ("mineral", "spectral"): "Iron 34%, Silicon 28%, Oxygen 22%, trace Nickel and Cobalt",
    ("mineral", "microscopy"): "Crystalline lattice structure, grain size 0.2mm avg",
    ("mineral", "mass_spec"): "Primary peaks at 56 (Fe), 28 (Si), 16 (O) amu",
    ("biological", "spectral"): "Carbon-based compound, absorption peaks at 280nm and 450nm",
    ("biological", "microscopy"): "Rod-shaped microorganisms, 2-5 microns, intact cell walls",
    ("biological", "culture"): "Growth detected after 48h at 25°C in nutrient broth",
    ("gas", "spectral"): "CH4 dominant, trace C2H6 and H2S",
    ("gas", "mass_spec"): "Primary peak at 16 (CH4), secondary at 30 (C2H6) amu",
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool()
def list_experiments(status: str | None = None) -> str:
    """List all experiments, optionally filtered by status (running/complete/pending)."""
    results = EXPERIMENTS
    if status:
        results = [e for e in results if e["status"] == status]
    return json.dumps(results)


@server.tool()
def get_sample(sample_id: str) -> str:
    """Get details for a specific sample by ID."""
    sample = SAMPLES.get(sample_id)
    if not sample:
        return json.dumps({"error": f"Unknown sample: {sample_id}"})
    return json.dumps({"sample_id": sample_id, **sample})


@server.tool()
def run_analysis(sample_id: str, method: str) -> str:
    """Run an analysis method on a sample. Returns analysis results."""
    sample = SAMPLES.get(sample_id)
    if not sample:
        return json.dumps({"error": f"Unknown sample: {sample_id}"})
    if method not in ANALYSIS_METHODS:
        known = ", ".join(ANALYSIS_METHODS.keys())
        return json.dumps({"error": f"Unknown method: {method}", "available": known})

    key = (sample["type"], method)
    finding = ANALYSIS_RESULTS.get(key, f"No specific results for {sample['type']} with {method}")

    return json.dumps({
        "sample_id": sample_id,
        "method": method,
        "method_description": ANALYSIS_METHODS[method],
        "result": finding,
    })


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Science Lab server starting at http://localhost:8000/mcp")
    server.run(transport="streamable-http")
