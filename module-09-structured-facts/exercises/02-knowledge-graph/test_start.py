"""Tests for Exercise 02 — Knowledge Graph."""

from __future__ import annotations

import pytest

from start import Entity, KnowledgeGraph, Relationship, build_graph, find_connections

FACTS = [
    {"subject": "Vasquez", "predicate": "repaired", "object": "thruster array"},
    {"subject": "Chen", "predicate": "plotted_avoidance", "object": "debris field"},
    {"subject": "Okafor", "predicate": "reported_radiation", "object": "cargo bay 2"},
    {"subject": "Vasquez", "predicate": "inspected", "object": "cargo bay 2"},
]


class TestKnowledgeGraph:
    def test_add_and_get_entity(self):
        g = KnowledgeGraph()
        g.add_entity(Entity("Vasquez", "crew"))
        assert g.get_entity("Vasquez") is not None
        assert g.get_entity("Vasquez").entity_type == "crew"

    def test_get_missing_entity(self):
        g = KnowledgeGraph()
        assert g.get_entity("nobody") is None

    def test_add_relationship(self):
        g = KnowledgeGraph()
        g.add_relationship(Relationship("A", "B", "knows"))
        assert len(g.edges) == 1

    def test_neighbours(self):
        g = KnowledgeGraph()
        g.add_relationship(Relationship("A", "B", "knows"))
        g.add_relationship(Relationship("C", "A", "trusts"))
        g.add_relationship(Relationship("D", "E", "other"))
        assert len(g.neighbours("A")) == 2
        assert len(g.neighbours("D")) == 1


class TestBuildGraph:
    def test_creates_entities(self):
        graph = build_graph(FACTS)
        assert graph.get_entity("Vasquez") is not None
        assert graph.get_entity("thruster array") is not None

    def test_creates_relationships(self):
        graph = build_graph(FACTS)
        assert len(graph.edges) == len(FACTS)

    def test_deduplicates_entities(self):
        graph = build_graph(FACTS)
        entity_names = list(graph.entities.keys())
        assert len(entity_names) == len(set(entity_names))


class TestFindConnections:
    def test_depth_zero_returns_direct(self):
        graph = build_graph(FACTS)
        rels = find_connections(graph, "Vasquez", max_depth=1)
        sources_and_targets = set()
        for r in rels:
            sources_and_targets.add(r.source)
            sources_and_targets.add(r.target)
        assert "Vasquez" in sources_and_targets

    def test_depth_two_reaches_further(self):
        graph = build_graph(FACTS)
        rels_1 = find_connections(graph, "Vasquez", max_depth=1)
        rels_2 = find_connections(graph, "Vasquez", max_depth=2)
        assert len(rels_2) >= len(rels_1)

    def test_unknown_entity_returns_empty(self):
        graph = build_graph(FACTS)
        assert find_connections(graph, "nobody") == []
