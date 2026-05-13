"""
Demo: Dataclasses and Protocols — OOP vs functional style for agent components.
Run:  python module-00-python-fundamentals/demo/03_dataclasses_protocols.py
"""

from dataclasses import dataclass, field
from typing import Protocol


# --- Dataclasses: structured, typed, with sensible defaults ---

@dataclass
class CrewMember:
    id: str
    name: str
    role: str
    department: str
    clearance_level: int = 1
    specializations: list[str] = field(default_factory=list)
    active_mission: str | None = None

    @property
    def is_available(self) -> bool:
        return self.active_mission is None

    def promote(self, new_clearance: int) -> "CrewMember":
        """Return a new CrewMember with updated clearance (immutable style)."""
        return CrewMember(
            id=self.id,
            name=self.name,
            role=self.role,
            department=self.department,
            clearance_level=new_clearance,
            specializations=self.specializations[:],
            active_mission=self.active_mission,
        )


# --- Protocol: structural subtyping (duck typing with type safety) ---

class Briefable(Protocol):
    """Anything that can produce a one-line status briefing."""

    def briefing(self) -> str: ...


@dataclass
class Mission:
    id: str
    name: str
    sector: str
    status: str
    risk_level: int

    def briefing(self) -> str:
        risk_bar = "*" * self.risk_level
        return f"[{self.status.upper()}] {self.name} @ {self.sector}  risk: {risk_bar}"


@dataclass
class ShipSystem:
    name: str
    online: bool
    efficiency: float

    def briefing(self) -> str:
        status = "ONLINE" if self.online else "OFFLINE"
        return f"[{status}] {self.name}  efficiency: {self.efficiency:.0%}"


def print_briefings(items: list[Briefable]) -> None:
    """Works with any object that has a .briefing() method — no inheritance needed."""
    print("\n--- Status briefings ---")
    for item in items:
        print(f"  {item.briefing()}")


if __name__ == "__main__":
    engineer = CrewMember(
        id="CRW-003",
        name="Chief Engineer Mira Chen",
        role="engineer",
        department="engineering",
        clearance_level=4,
        specializations=["propulsion", "shields"],
        active_mission="MSN-001",
    )
    print(f"Engineer: {engineer}")
    print(f"Available? {engineer.is_available}")

    promoted = engineer.promote(5)
    print(f"After promotion: clearance {promoted.clearance_level}")
    print(f"Original unchanged: clearance {engineer.clearance_level}")

    mission = Mission("MSN-003", "Void Cartography", "Boötes Void", "active", 5)
    warp_core = ShipSystem("Warp Core", online=True, efficiency=0.97)
    shields = ShipSystem("Shields", online=True, efficiency=0.85)
    sensors = ShipSystem("Long-Range Sensors", online=False, efficiency=0.0)

    print_briefings([mission, warp_core, shields, sensors])
