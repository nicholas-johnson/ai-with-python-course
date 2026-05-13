"""Tests for Exercise 03 — RAG Chain."""

import pytest

from start import ask


@pytest.mark.skip(reason="Skeleton — implement ask")
def test_ask_returns_answer():
    result = ask("What are the navigation protocols for sector 7?")
    assert isinstance(result, str)
    assert len(result) > 0
