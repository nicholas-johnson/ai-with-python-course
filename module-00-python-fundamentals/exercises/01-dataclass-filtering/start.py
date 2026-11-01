"""
Exercise 01 — Crew Manifest
Parse crew JSON into dataclasses, filter by field values, and format a roster.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CrewMember:
    """One crew record from data/crew.json."""

    # TODO: id (str), name (str), role (str), department (str),
    #       clearance_level (int, default 1),
    #       specializations (list[str], default empty -- use field(default_factory=list)),
    #       active_mission (str | None, default None)
    pass


def load_crew(path: Path) -> list[CrewMember]:
    """Read crew.json and return a list of CrewMember instances."""
    # TODO: json.loads(path.read_text()), then build a CrewMember from each dict.
    #       Note the JSON keys are camelCase: clearanceLevel, activeMission.
    pass


def filter_crew(
    crew: list[CrewMember],
    department: str | None = None,
    min_clearance: int = 0,
) -> list[CrewMember]:
    """Keep members in `department` (if given) with clearance >= min_clearance."""
    # TODO: apply each filter only when it is set
    pass


def format_roster(crew: list[CrewMember]) -> str:
    """One line per member: "Name (role) — clearance N"."""
    # TODO: build the lines and join them with newlines
    pass


def main() -> None:
    """Load the crew manifest and print a couple of rosters."""
    data_path = Path(__file__).resolve().parents[3] / "data" / "crew.json"
    crew = load_crew(data_path)
    print(f"Loaded {len(crew)} crew members\n")
    print("Full roster:")
    print(format_roster(crew))
    print("\nScience department, clearance >= 3:")
    print(format_roster(filter_crew(crew, department="science", min_clearance=3)))


if __name__ == "__main__":
    main()
