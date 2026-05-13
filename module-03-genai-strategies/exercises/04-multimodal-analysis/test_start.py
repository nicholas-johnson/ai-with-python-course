"""Tests for Exercise 04 — Multimodal Analysis."""

from __future__ import annotations

import base64
import json

import pytest

from start import parse_damage_report, prepare_audio_payload, prepare_image_message


class TestPrepareImageMessage:
    def test_returns_user_role(self):
        msg = prepare_image_message(b"fakepng")
        assert msg["role"] == "user"

    def test_contains_text_part(self):
        msg = prepare_image_message(b"fakepng", prompt="Check hull")
        parts = msg["content"]
        text_parts = [p for p in parts if p.get("type") == "text"]
        assert len(text_parts) == 1
        assert text_parts[0]["text"] == "Check hull"

    def test_contains_image_url_part_with_base64(self):
        raw = b"fakepng"
        msg = prepare_image_message(raw, media_type="image/png")
        parts = msg["content"]
        img_parts = [p for p in parts if p.get("type") == "image_url"]
        assert len(img_parts) == 1
        url = img_parts[0]["image_url"]["url"]
        expected_b64 = base64.b64encode(raw).decode()
        assert url == f"data:image/png;base64,{expected_b64}"

    def test_custom_media_type(self):
        msg = prepare_image_message(b"fakejpg", media_type="image/jpeg")
        url = msg["content"][1]["image_url"]["url"]
        assert url.startswith("data:image/jpeg;base64,")


class TestPrepareAudioPayload:
    def test_contains_file_bytes(self):
        payload = prepare_audio_payload(b"audio-data")
        assert payload["file"] == b"audio-data"

    def test_contains_filename(self):
        payload = prepare_audio_payload(b"audio-data", filename="log.wav")
        assert payload["filename"] == "log.wav"

    def test_contains_model_key(self):
        payload = prepare_audio_payload(b"audio-data")
        assert "model" in payload


class TestParseDamageReport:
    def test_valid_report(self):
        raw = json.dumps({
            "location": "Deck 7, port hull",
            "severity": "high",
            "description": "Micro-fractures detected along weld seam.",
        })
        report = parse_damage_report(raw)
        assert report["location"] == "Deck 7, port hull"
        assert report["severity"] == "high"

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_damage_report("not json at all")

    def test_missing_key_raises(self):
        raw = json.dumps({"location": "Deck 3", "severity": "low"})
        with pytest.raises(ValueError, match="Missing required key"):
            parse_damage_report(raw)

    def test_invalid_severity_raises(self):
        raw = json.dumps({
            "location": "Deck 3",
            "severity": "extreme",
            "description": "Total breach.",
        })
        with pytest.raises(ValueError, match="Invalid severity"):
            parse_damage_report(raw)
