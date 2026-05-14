"""Tests for Exercise 01 — Retrieval Router."""

from __future__ import annotations

import pytest

from start import RetrievalBackend, RoutingDecision, classify_query, route_and_retrieve


class TestClassifyQuery:
    def test_relationship_query_routes_to_graph(self):
        decision = classify_query("What is the relationship between Vasquez and the thruster?")
        assert decision.backend == RetrievalBackend.GRAPH

    def test_who_query_routes_to_graph(self):
        decision = classify_query("Who reported the cargo bay incident?")
        assert decision.backend == RetrievalBackend.GRAPH

    def test_error_code_routes_to_keyword(self):
        decision = classify_query("Find error code E-4417 in the logs")
        assert decision.backend == RetrievalBackend.KEYWORD

    def test_log_entry_routes_to_keyword(self):
        decision = classify_query("Show log entry for sensor array 7")
        assert decision.backend == RetrievalBackend.KEYWORD

    def test_general_query_routes_to_vector(self):
        decision = classify_query("How does radiation shielding work on the Pathfinder?")
        assert decision.backend == RetrievalBackend.VECTOR

    def test_returns_routing_decision(self):
        decision = classify_query("anything")
        assert isinstance(decision, RoutingDecision)
        assert 0.0 <= decision.confidence <= 1.0
        assert decision.reasoning


class TestRouteAndRetrieve:
    def test_dispatches_to_correct_backend(self):
        called_with = {}

        def mock_vector(q):
            called_with["vector"] = q
            return [{"content": "vector result"}]

        def mock_graph(q):
            called_with["graph"] = q
            return [{"content": "graph result"}]

        def mock_keyword(q):
            called_with["keyword"] = q
            return [{"content": "keyword result"}]

        backends = {
            RetrievalBackend.VECTOR: mock_vector,
            RetrievalBackend.GRAPH: mock_graph,
            RetrievalBackend.KEYWORD: mock_keyword,
        }

        results = route_and_retrieve("Who fixed the engine?", backends)
        assert "graph" in called_with
        assert len(results) > 0

    def test_returns_list(self):
        backends = {
            RetrievalBackend.VECTOR: lambda q: [{"content": "v"}],
            RetrievalBackend.GRAPH: lambda q: [{"content": "g"}],
            RetrievalBackend.KEYWORD: lambda q: [{"content": "k"}],
        }
        results = route_and_retrieve("general question", backends)
        assert isinstance(results, list)
