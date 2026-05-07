"""Tests for Exercise 03 — RAG Pipeline."""

import pytest

from start import run_rag


class _FakeRetriever:
    def search(self, query: str, k: int):
        return [{"id": "c1", "text": "Pathfinder departed drydock 2347."}]


@pytest.mark.skip(reason="Skeleton — implement run_rag in start.py")
def test_run_rag_returns_answer_and_citations():
    out = run_rag("When did we leave?", _FakeRetriever(), k=2)
    assert "answer" in out and "citations" in out
