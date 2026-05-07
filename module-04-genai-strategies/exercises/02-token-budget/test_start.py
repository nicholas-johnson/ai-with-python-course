"""Tests for Exercise 02 — Token Budget."""

import pytest

from start import count_tokens, enforce_budget


@pytest.mark.skip(reason="Skeleton — implement count_tokens and enforce_budget")
def test_enforce_budget_drops_old_messages():
    msgs = ["a " * 50, "b " * 50, "c"]
    budgeted = enforce_budget(msgs, max_tokens=30)
    assert len(budgeted) >= 1
    assert count_tokens("hello") >= 1
