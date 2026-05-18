"""Tests for Exercise 02 — Tool Agent."""

import pytest

from start import run_agent


@pytest.mark.skip(reason="Skeleton — implement run_agent")
def test_run_agent_returns_string():
    result = run_agent("What is the current docking seal integrity?")
    assert isinstance(result, str)
    assert len(result) > 0
