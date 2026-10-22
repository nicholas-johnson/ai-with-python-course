"""Shared pytest fixtures for Deep Space Ops exercises."""

import json
from pathlib import Path
from unittest.mock import MagicMock

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


@pytest.fixture()
def fake_parse():
    """Build a stand-in for client.responses.parse from JSON fixtures.

    Each call validates the next JSON string against the requested
    text_format model (the last one repeats), so a fixture that doesn't
    match the schema fails the test the same way a real response would.

        mock_client.responses.parse.side_effect = fake_parse(PLAN_JSON)
    """

    def factory(*json_texts: str):
        calls = {"n": 0}

        def _parse(*, text_format, **kwargs):
            text = json_texts[min(calls["n"], len(json_texts) - 1)]
            calls["n"] += 1
            return MagicMock(
                output_text=text,
                output_parsed=text_format.model_validate_json(text),
            )

        return _parse

    return factory
