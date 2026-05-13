"""Tests for Exercise 02 — Conversation Summary."""

import pytest

from start import summarise_turns, trim_turns


@pytest.mark.skip(reason="Skeleton — implement trim_turns and summarise_turns")
def test_trim_turns_respects_budget():
    turns = [{"role": "user", "content": "word " * 100}]
    trimmed = trim_turns(turns, max_tokens=20)
    assert len(trimmed) <= len(turns)


@pytest.mark.skip(reason="Skeleton — implement summarise_turns")
def test_summary_under_budget():
    turns = [{"role": "user", "content": "alpha beta gamma"}]
    s = summarise_turns(turns, max_tokens=10)
    assert isinstance(s, str) and len(s) > 0
