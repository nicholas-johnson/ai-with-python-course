"""Shared pytest fixtures for Deep Space Ops exercises."""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture()
def missions():
    return json.loads((DATA_DIR / "missions.json").read_text())


@pytest.fixture()
def crew():
    return json.loads((DATA_DIR / "crew.json").read_text())


@pytest.fixture()
def star_systems():
    return json.loads((DATA_DIR / "star_systems.json").read_text())


@pytest.fixture()
def ship_logs():
    return json.loads((DATA_DIR / "ship_logs.json").read_text())
