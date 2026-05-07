"""Tests for Exercise 01 — Memory Store."""

import pytest

from start import LongTermMemory, SessionMemory


@pytest.mark.skip(reason="Skeleton — implement SessionMemory and LongTermMemory")
def test_session_memory_keeps_turns():
    s = SessionMemory()
    s.add_turn("user", "hello")
    assert len(s.get_context()) == 1


@pytest.mark.skip(reason="Skeleton — implement decay and recall")
def test_long_term_decay():
    m = LongTermMemory()
    m.remember("prefs", "dark mode")
    m.tick_decay(0.5)
    hits = m.recall("prefs")
    assert isinstance(hits, list)
