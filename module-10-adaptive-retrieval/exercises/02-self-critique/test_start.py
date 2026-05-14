"""Tests for Exercise 02 — Self-Critique Retrieval."""

from __future__ import annotations

import pytest

from start import CritiqueResult, RetrievedDoc, critique_results, refine_query, retrieval_loop


class TestCritiqueResults:
    def test_sufficient_when_above_threshold(self):
        docs = [
            RetrievedDoc("a", "s1", 0.8),
            RetrievedDoc("b", "s2", 0.7),
        ]
        result = critique_results("q", docs, threshold=0.6)
        assert result.is_sufficient is True
        assert result.avg_relevance >= 0.6

    def test_insufficient_when_below_threshold(self):
        docs = [
            RetrievedDoc("a", "s1", 0.3),
            RetrievedDoc("b", "s2", 0.4),
        ]
        result = critique_results("q", docs, threshold=0.6)
        assert result.is_sufficient is False

    def test_empty_docs_insufficient(self):
        result = critique_results("q", [], threshold=0.6)
        assert result.is_sufficient is False
        assert result.avg_relevance == 0.0

    def test_returns_critique_result(self):
        docs = [RetrievedDoc("a", "s1", 0.5)]
        result = critique_results("q", docs)
        assert isinstance(result, CritiqueResult)
        assert isinstance(result.suggestion, str)


class TestRefineQuery:
    def test_returns_different_query(self):
        critique = CritiqueResult(False, 0.4, "needs refinement")
        refined = refine_query("original query", critique)
        assert refined != "original query"
        assert len(refined) > len("original query")


class TestRetrievalLoop:
    def test_stops_early_on_good_results(self):
        def good_retrieve(q):
            return [RetrievedDoc("good", "s1", 0.9)]

        docs, attempts = retrieval_loop("q", good_retrieve, max_attempts=3, threshold=0.6)
        assert attempts == 1
        assert len(docs) > 0

    def test_retries_on_poor_results(self):
        call_count = 0

        def improving_retrieve(q):
            nonlocal call_count
            call_count += 1
            score = 0.3 + (call_count * 0.2)
            return [RetrievedDoc("doc", "s1", min(score, 1.0))]

        docs, attempts = retrieval_loop("q", improving_retrieve, max_attempts=3, threshold=0.6)
        assert attempts >= 2

    def test_respects_max_attempts(self):
        def bad_retrieve(q):
            return [RetrievedDoc("bad", "s1", 0.1)]

        docs, attempts = retrieval_loop("q", bad_retrieve, max_attempts=2, threshold=0.9)
        assert attempts == 2

    def test_returns_docs_and_count(self):
        def retrieve(q):
            return [RetrievedDoc("x", "s1", 0.8)]

        result = retrieval_loop("q", retrieve)
        assert isinstance(result, tuple)
        assert len(result) == 2
