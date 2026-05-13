"""Tests for Exercise 02 — Vision."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from start import MissionReport, encode_image, detect_mime, analyse_image

TEST_IMAGE = Path(__file__).parent / "test_image.png"


# ---- encode_image tests ----------------------------------------------------

def test_encode_image_returns_base64():
    b64 = encode_image(TEST_IMAGE)
    raw = base64.b64decode(b64)
    assert raw[:4] == b"\x89PNG"


def test_encode_image_roundtrips():
    b64 = encode_image(TEST_IMAGE)
    decoded = base64.b64decode(b64)
    assert decoded == TEST_IMAGE.read_bytes()


# ---- detect_mime tests ------------------------------------------------------

def test_detect_mime_png():
    assert detect_mime("photo.png") == "image/png"


def test_detect_mime_jpeg():
    assert detect_mime("photo.jpg") == "image/jpeg"


def test_detect_mime_default():
    assert detect_mime("no_extension") == "image/png"


# ---- analyse_image tests (mocked) ------------------------------------------

def _make_mock_client(response_json: dict) -> MagicMock:
    mock = MagicMock()
    choice = MagicMock()
    choice.message.content = json.dumps(response_json)
    mock.chat.completions.create.return_value = MagicMock(choices=[choice])
    return mock


VALID_REPORT = {
    "mission_id": "VIS-1",
    "status": "active",
    "risk_level": "medium",
    "summary": "Structural damage detected on starboard hull.",
}


def test_analyse_image_local_file():
    client = _make_mock_client(VALID_REPORT)
    report = analyse_image(client, str(TEST_IMAGE))
    assert isinstance(report, MissionReport)
    assert report.mission_id == "VIS-1"

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = messages[-1]
    assert user_msg["role"] == "user"
    assert isinstance(user_msg["content"], list)
    assert len(user_msg["content"]) == 2
    assert user_msg["content"][0]["type"] == "text"
    assert user_msg["content"][1]["type"] == "image_url"
    url = user_msg["content"][1]["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")


def test_analyse_image_url():
    client = _make_mock_client(VALID_REPORT)
    url = "https://example.com/photo.jpg"
    report = analyse_image(client, url)
    assert isinstance(report, MissionReport)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]
    user_msg = messages[-1]
    image_part = user_msg["content"][1]
    assert image_part["image_url"]["url"] == url


def test_analyse_image_uses_json_mode():
    client = _make_mock_client(VALID_REPORT)
    analyse_image(client, str(TEST_IMAGE))
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs.get("response_format") == {"type": "json_object"}


# ---- Integration test (requires API key) -----------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_analyse_image_integration():
    import openai

    client = openai.OpenAI()
    report = analyse_image(client, str(TEST_IMAGE), "Describe what you see.")
    assert isinstance(report, MissionReport)
    assert report.status in {"active", "completed", "aborted"}
