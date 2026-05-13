"""
Demo: Python data structures with crew and mission data.
Run:  python module-00-python-fundamentals/demo/01_data_structures.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

crew = json.loads((DATA_DIR / "crew.json").read_text())
missions = json.loads((DATA_DIR / "missions.json").read_text())


# --- Lists: ordered, mutable, iterable ---

crew_names = [member["name"] for member in crew]
print("Crew roster:", crew_names[:5], "...")

active_crew = [m for m in crew if m["activeMission"] is not None]
print(f"Active crew: {len(active_crew)} / {len(crew)}")

high_clearance = [m for m in crew if m["clearanceLevel"] >= 4]
print("High-clearance personnel:", [m["name"] for m in high_clearance])


# --- Dicts: key-value lookup, O(1) access ---

crew_by_id = {m["id"]: m for m in crew}
print(f"\nLookup CRW-003: {crew_by_id['CRW-003']['name']}")

dept_counts: dict[str, int] = {}
for member in crew:
    dept = member["department"]
    dept_counts[dept] = dept_counts.get(dept, 0) + 1
print("Department headcounts:", dept_counts)


# --- Sets: unique elements, fast membership, set algebra ---

all_specializations: set[str] = set()
for member in crew:
    all_specializations.update(member["specializations"])
print(f"\nUnique specializations across crew: {len(all_specializations)}")

science_specs = {s for m in crew if m["department"] == "science" for s in m["specializations"]}
eng_specs = {s for m in crew if m["department"] == "engineering" for s in m["specializations"]}
print("Science-only skills:", science_specs - eng_specs)
print("Shared skills:", science_specs & eng_specs)


# --- Tuples: immutable sequences, good for fixed records ---

mission_summaries = [
    (m["id"], m["name"], m["status"], m["riskLevel"])
    for m in missions
]
print("\nMission summaries (id, name, status, risk):")
for mid, name, status, risk in mission_summaries:
    risk_bar = "*" * risk
    print(f"  {mid}  {name:<30} {status:<12} risk: {risk_bar}")
