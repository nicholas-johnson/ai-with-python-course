"""Tests for Exercise 03 — ReAct Loop."""

import pytest

from start import run_react


@pytest.mark.skip(reason="Skeleton — implement run_react and TOOLS")
def test_run_react_returns_trace():
    trace = run_react("What is sensor S1?", max_steps=3)
    assert isinstance(trace, list)
