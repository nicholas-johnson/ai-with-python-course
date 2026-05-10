"""
Exercise 01 — Crew Manifest (solution)
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CrewMember:
    id: str
    name: str
    role: str
    department: str
    clearance_level: int = 1
    specializations: list[str] = field(default_factory=list)
    active_mission: str | None = None


def load_crew(path: Path) -> list[CrewMember]:
    raw = json.loads(path.read_text())
    return [
        CrewMember(
            id=r["id"],
            name=r["name"],
            role=r["role"],
            department=r["department"],
            clearance_level=r["clearanceLevel"],
            specializations=r.get("specializations", []),
            active_mission=r.get("activeMission"),
        )
        for r in raw
    ]


def filter_crew(
    crew: list[CrewMember],
    department: str | None = None,
    min_clearance: int = 0,
) -> list[CrewMember]:
    result = crew
    if department:
        result = [m for m in result if m.department == department]
    if min_clearance > 0:
        result = [m for m in result if m.clearance_level >= min_clearance]
    return result


def format_roster(crew: list[CrewMember]) -> str:
    lines = [
        f"{m.name} ({m.role}) \u2014 clearance {m.clearance_level}"
        for m in crew
    ]
    return "\n".join(lines)
