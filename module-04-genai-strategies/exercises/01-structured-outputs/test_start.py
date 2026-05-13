"""Tests for Exercise 01 — Structured Outputs."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from start import MissionReport, SYSTEM_PROMPT, analyse


# ---- Model tests -----------------------------------------------------------

def test_mission_report_valid():
    report = MissionReport(
        mission_id="KS-7",
        status="active",
        risk_level="high",
        summary="Kepler sweep in progress.",
    )
    assert report.mission_id == "KS-7"
    assert report.status == "active"


def test_mission_report_rejects_bad_status():
    with pytest.raises(ValidationError):
        MissionReport(
            mission_id="KS-7",
            status="unknown",
            risk_level="high",
            summary="Bad status.",
        )


def test_mission_report_rejects_bad_risk_level():
    with pytest.raises(ValidationError):
        MissionReport(
            mission_id="KS-7",
            status="active",
            risk_level="extreme",
            summary="Bad risk.",
        )


# ---- System prompt tests ---------------------------------------------------

def test_system_prompt_is_nonempty():
    assert len(SYSTEM_PROMPT) > 20, "SYSTEM_PROMPT should describe the expected JSON schema"


def test_system_prompt_mentions_json():
    lower = SYSTEM_PROMPT.lower()
    assert "json" in lower, "SYSTEM_PROMPT should mention JSON"


# ---- analyse() tests (mocked) ---------------------------------------------

def _make_mock_client(response_json: dict) -> MagicMock:
    mock = MagicMock()
    choice = MagicMock()
    choice.message.content = json.dumps(response_json)
    mock.chat.completions.create.return_value = MagicMock(choices=[choice])
    return mock


def test_analyse_returns_mission_report():
    payload = {
        "mission_id": "MS-42",
        "status": "completed",
        "risk_level": "low",
        "summary": "Survey completed without incident.",
    }
    client = _make_mock_client(payload)
    report = analyse(client, "The survey finished uneventfully.")
    assert isinstance(report, MissionReport)
    assert report.mission_id == "MS-42"
    assert report.status == "completed"


def test_analyse_uses_json_mode():
    payload = {
        "mission_id": "MS-1",
        "status": "active",
        "risk_level": "medium",
        "summary": "Test.",
    }
    client = _make_mock_client(payload)
    analyse(client, "test")
    call_kwargs = client.chat.completions.create.call_args
    assert call_kwargs.kwargs.get("response_format") == {"type": "json_object"}


def test_analyse_raises_on_invalid_json():
    mock = MagicMock()
    choice = MagicMock()
    choice.message.content = "not json at all"
    mock.chat.completions.create.return_value = MagicMock(choices=[choice])
    with pytest.raises(Exception):
        analyse(mock, "bad input")


# ---- Integration test (requires API key) -----------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_analyse_integration():
    import openai

    client = openai.OpenAI()
    report = analyse(client, "The Kepler sweep lost contact at 14:30 UTC.")
    assert isinstance(report, MissionReport)
    assert report.status in {"active", "completed", "aborted"}
    assert report.risk_level in {"low", "medium", "high", "critical"}
