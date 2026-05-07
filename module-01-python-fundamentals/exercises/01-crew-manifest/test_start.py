"""Tests for Exercise 01 — Crew Manifest."""

from pathlib import Path

import pytest

from start import CrewMember, filter_crew, format_roster, load_crew

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
CREW_PATH = DATA_DIR / "crew.json"


class TestCrewMember:
    def test_dataclass_fields(self):
        member = CrewMember(
            id="CRW-099",
            name="Test Pilot",
            role="navigator",
            department="operations",
            clearance_level=3,
            specializations=["stellar-cartography"],
            active_mission="MSN-001",
        )
        assert member.id == "CRW-099"
        assert member.name == "Test Pilot"
        assert member.department == "operations"
        assert member.clearance_level == 3
        assert member.specializations == ["stellar-cartography"]
        assert member.active_mission == "MSN-001"

    def test_default_values(self):
        member = CrewMember(id="CRW-100", name="Rookie", role="ops", department="operations")
        assert member.clearance_level == 1
        assert member.specializations == []
        assert member.active_mission is None

    def test_mutable_default_not_shared(self):
        a = CrewMember(id="A", name="A", role="ops", department="operations")
        b = CrewMember(id="B", name="B", role="ops", department="operations")
        a.specializations.append("comms")
        assert "comms" not in b.specializations


class TestLoadCrew:
    def test_returns_list_of_crew_members(self):
        crew = load_crew(CREW_PATH)
        assert isinstance(crew, list)
        assert len(crew) > 0
        assert all(isinstance(m, CrewMember) for m in crew)

    def test_loads_known_member(self):
        crew = load_crew(CREW_PATH)
        voss = next((m for m in crew if m.id == "CRW-001"), None)
        assert voss is not None
        assert "Voss" in voss.name
        assert voss.role == "captain"
        assert voss.clearance_level == 5


class TestFilterCrew:
    @pytest.fixture()
    def crew(self):
        return load_crew(CREW_PATH)

    def test_filter_by_department(self, crew):
        science = filter_crew(crew, department="science")
        assert len(science) > 0
        assert all(m.department == "science" for m in science)

    def test_filter_by_clearance(self, crew):
        high = filter_crew(crew, min_clearance=4)
        assert len(high) > 0
        assert all(m.clearance_level >= 4 for m in high)

    def test_combined_filter(self, crew):
        result = filter_crew(crew, department="operations", min_clearance=3)
        assert all(m.department == "operations" and m.clearance_level >= 3 for m in result)

    def test_no_filters_returns_all(self, crew):
        assert filter_crew(crew) == crew


class TestFormatRoster:
    def test_format_single_member(self):
        crew = [CrewMember(id="X", name="Alice", role="engineer", department="eng", clearance_level=3)]
        result = format_roster(crew)
        assert "Alice" in result
        assert "engineer" in result
        assert "3" in result

    def test_format_multiple_members(self):
        crew = [
            CrewMember(id="A", name="Alice", role="engineer", department="eng", clearance_level=3),
            CrewMember(id="B", name="Bob", role="captain", department="cmd", clearance_level=5),
        ]
        result = format_roster(crew)
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_empty_list(self):
        assert format_roster([]) == ""
