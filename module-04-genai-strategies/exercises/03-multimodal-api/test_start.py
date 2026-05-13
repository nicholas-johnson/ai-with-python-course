"""Tests for Exercise 03 — Multimodal API."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from start import app, MissionReport

client = TestClient(app)

VALID_REPORT = {
    "mission_id": "API-1",
    "status": "active",
    "risk_level": "medium",
    "summary": "Test report from mocked LLM.",
}


def _mock_openai_client(report: dict = VALID_REPORT) -> MagicMock:
    mock = MagicMock()
    choice = MagicMock()
    choice.message.content = json.dumps(report)
    mock.chat.completions.create.return_value = MagicMock(choices=[choice])
    transcript_mock = MagicMock()
    transcript_mock.text = "This is a test transcript."
    mock.audio.transcriptions.create.return_value = transcript_mock
    return mock


# ---- /health ---------------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---- /chat -----------------------------------------------------------------

def test_chat_returns_mission_report():
    mock = _mock_openai_client()
    with patch("start._get_client", return_value=mock):
        resp = client.post("/chat", json={"text": "All systems nominal."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mission_id"] == "API-1"
    assert data["status"] == "active"


def test_chat_calls_openai():
    mock = _mock_openai_client()
    with patch("start._get_client", return_value=mock):
        client.post("/chat", json={"text": "Test."})
    mock.chat.completions.create.assert_called_once()


# ---- /vision ---------------------------------------------------------------

def test_vision_with_base64():
    mock = _mock_openai_client()
    fake_b64 = base64.b64encode(b"\x89PNG fake image").decode()
    with patch("start._get_client", return_value=mock):
        resp = client.post("/vision", json={"image": fake_b64})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mission_id"] == "API-1"


def test_vision_with_url():
    mock = _mock_openai_client()
    with patch("start._get_client", return_value=mock):
        resp = client.post(
            "/vision",
            json={"image_url": "https://example.com/photo.jpg"},
        )
    assert resp.status_code == 200


def test_vision_no_image_returns_400():
    mock = _mock_openai_client()
    with patch("start._get_client", return_value=mock):
        resp = client.post("/vision", json={})
    assert resp.status_code == 400


# ---- /transcribe -----------------------------------------------------------

def test_transcribe_returns_text():
    mock = _mock_openai_client()
    fake_audio = b"RIFF" + b"\x00" * 100
    with patch("start._get_client", return_value=mock):
        resp = client.post(
            "/transcribe",
            files={"file": ("test.wav", fake_audio, "audio/wav")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["transcript"] == "This is a test transcript."


def test_transcribe_calls_whisper():
    mock = _mock_openai_client()
    fake_audio = b"RIFF" + b"\x00" * 100
    with patch("start._get_client", return_value=mock):
        client.post(
            "/transcribe",
            files={"file": ("test.wav", fake_audio, "audio/wav")},
        )
    mock.audio.transcriptions.create.assert_called_once()


# ---- Integration tests (require API key) -----------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_chat_integration():
    resp = client.post("/chat", json={"text": "Minor hull scratch on deck 7."})
    assert resp.status_code == 200
    data = resp.json()
    report = MissionReport.model_validate(data)
    assert report.status in {"active", "completed", "aborted"}
