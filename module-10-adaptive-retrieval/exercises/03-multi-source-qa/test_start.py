"""Tests for Exercise 03 — Multi-Source QA."""

from __future__ import annotations

import json

import pytest

from start import Answer, SearchResult, fan_out, merge_and_rank, multi_source_qa


def mock_vector(q):
    return [
        SearchResult("Thruster protocol", "vector", "v1", 0.88),
        SearchResult("Engine safety", "vector", "v2", 0.72),
    ]


def mock_graph(q):
    return [
        SearchResult("Vasquez repaired thruster", "graph", "g1", 0.91),
    ]


def mock_keyword(q):
    return [
        SearchResult("Log 4417: thruster offline", "keyword", "k1", 0.80),
        SearchResult("Thruster protocol", "keyword", "v1", 0.75),  # duplicate source_id
    ]


BACKENDS = {"vector": mock_vector, "graph": mock_graph, "keyword": mock_keyword}


def mock_llm(prompt):
    return json.dumps({"answer": "Vasquez repaired it.", "confidence": 0.9})


class TestFanOut:
    def test_queries_all_backends(self):
        results = fan_out("test", BACKENDS)
        assert "vector" in results
        assert "graph" in results
        assert "keyword" in results

    def test_returns_search_results(self):
        results = fan_out("test", BACKENDS)
        for name, items in results.items():
            assert all(isinstance(r, SearchResult) for r in items)


class TestMergeAndRank:
    def test_deduplicates_by_source_id(self):
        result_sets = fan_out("test", BACKENDS)
        merged = merge_and_rank(result_sets)
        ids = [r.source_id for r in merged]
        assert len(ids) == len(set(ids))

    def test_sorted_by_score_descending(self):
        result_sets = fan_out("test", BACKENDS)
        merged = merge_and_rank(result_sets)
        scores = [r.score for r in merged]
        assert scores == sorted(scores, reverse=True)

    def test_empty_inputs(self):
        assert merge_and_rank({}) == []


class TestMultiSourceQa:
    def test_returns_answer(self):
        result = multi_source_qa("thruster repair", BACKENDS, mock_llm)
        assert isinstance(result, Answer)
        assert result.confidence > 0
        assert result.text

    def test_includes_sources(self):
        result = multi_source_qa("thruster repair", BACKENDS, mock_llm)
        assert len(result.sources) > 0

    def test_no_results_returns_zero_confidence(self):
        empty_backends = {"empty": lambda q: []}
        result = multi_source_qa("unknown", empty_backends, mock_llm)
        assert result.confidence == 0.0
