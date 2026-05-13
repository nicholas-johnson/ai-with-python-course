"""Tests for Exercise 03 — Grounded QA."""

from __future__ import annotations

import json

import pytest

from start import (
    Citation,
    Entity,
    GroundedAnswer,
    KnowledgeGraph,
    Relationship,
    build_grounded_prompt,
    grounded_qa,
    retrieve_relevant,
)


@pytest.fixture
def sample_graph() -> KnowledgeGraph:
    g = KnowledgeGraph()
    g.add_entity(Entity("Vasquez", "crew"))
    g.add_entity(Entity("thruster array", "system"))
    g.add_entity(Entity("cargo bay 2", "location"))
    g.add_entity(Entity("Okafor", "crew"))
    g.add_relationship(Relationship("Vasquez", "thruster array", "repaired"))
    g.add_relationship(Relationship("Vasquez", "cargo bay 2", "inspected"))
    g.add_relationship(Relationship("Okafor", "cargo bay 2", "reported_radiation"))
    return g


def mock_llm(prompt: str) -> str:
    return json.dumps({
        "answer": "Vasquez repaired the thruster array.",
        "citations": ["graph:Vasquez:repaired:thruster array"],
        "confidence": 0.92,
    })


class TestRetrieveRelevant:
    def test_finds_matching_entity(self, sample_graph):
        evidence = retrieve_relevant(sample_graph, "What did Vasquez do?")
        assert len(evidence) > 0
        assert all("source_id" in e for e in evidence)

    def test_no_match_returns_empty(self, sample_graph):
        evidence = retrieve_relevant(sample_graph, "What about the warp drive?")
        assert evidence == []

    def test_respects_top_k(self, sample_graph):
        evidence = retrieve_relevant(sample_graph, "What did Vasquez do?", top_k=1)
        assert len(evidence) <= 1


class TestBuildGroundedPrompt:
    def test_includes_question(self):
        prompt = build_grounded_prompt("test?", [{"source_id": "s1", "text": "fact"}])
        assert "test?" in prompt

    def test_includes_evidence(self):
        evidence = [{"source_id": "s1", "text": "important fact"}]
        prompt = build_grounded_prompt("q?", evidence)
        assert "important fact" in prompt


class TestGroundedQa:
    def test_returns_grounded_answer(self, sample_graph):
        result = grounded_qa("What did Vasquez do?", sample_graph, mock_llm)
        assert isinstance(result, GroundedAnswer)
        assert result.confidence > 0
        assert len(result.citations) > 0

    def test_no_evidence_returns_zero_confidence(self, sample_graph):
        result = grounded_qa("What about the warp drive?", sample_graph, mock_llm)
        assert result.confidence == 0.0

    def test_citations_have_source_ids(self, sample_graph):
        result = grounded_qa("What did Vasquez do?", sample_graph, mock_llm)
        for citation in result.citations:
            assert isinstance(citation, Citation)
            assert citation.source_id
