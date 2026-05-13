"""Tests for Exercise 03 — Guardrail Chain."""

import pytest

from start import run_guardrails


@pytest.mark.skip(reason="Skeleton — implement run_guardrails")
def test_guardrails_rejects_low_confidence():
    raw = {"answer": "ok", "confidence": 0.1}
    out = run_guardrails(raw, min_confidence=0.9)
    assert out.get("ok") is False or "errors" in out
