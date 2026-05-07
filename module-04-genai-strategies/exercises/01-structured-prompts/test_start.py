"""Tests for Exercise 01 — Structured Prompts."""

import pytest

from start import build_prompt, parse_mission_status


@pytest.mark.skip(reason="Skeleton — implement build_prompt and parse_mission_status")
def test_parse_valid_json_payload():
    prompt = build_prompt("Status check")
    assert "json" in prompt.lower() or "{" in prompt
    raw = '{"status":"nominal","code":200}'
    out = parse_mission_status(raw)
    assert out.get("status") == "nominal"
