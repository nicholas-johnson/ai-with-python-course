"""Tests for Exercise 02 — Batch Pipeline."""

import pytest

from start import TransientError, complete_batch


@pytest.mark.skip(reason="Skeleton — implement complete_batch")
def test_complete_batch_uses_fallback_after_retries():
    calls = {"n": 0}

    def primary(p):
        calls["n"] += 1
        raise TransientError("busy")

    def fallback(p):
        return "fallback:" + p

    out = complete_batch(["a"], primary, fallback, max_retries=2)
    assert out[0].startswith("fallback:")
