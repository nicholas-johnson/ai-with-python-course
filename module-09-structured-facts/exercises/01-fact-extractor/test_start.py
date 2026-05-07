"""Tests for Exercise 01 — Fact Extractor."""

from __future__ import annotations

import json

import pytest

from start import Fact, build_extraction_prompt, extract_facts, parse_llm_response, validate_facts

SAMPLE_LOG = (
    "Chief Engineer Vasquez repaired the port thruster array. "
    "Dr. Okafor reported elevated radiation in cargo bay 2."
)

MOCK_LLM_RESPONSE = json.dumps([
    {
        "subject": "Chief Engineer Vasquez",
        "predicate": "repaired",
        "object": "port thruster array",
        "source_text": "Chief Engineer Vasquez repaired the port thruster array.",
        "confidence": 0.95,
    },
    {
        "subject": "Dr. Okafor",
        "predicate": "reported",
        "object": "elevated radiation in cargo bay 2",
        "source_text": "Dr. Okafor reported elevated radiation in cargo bay 2.",
        "confidence": 0.90,
    },
])


def mock_llm(prompt: str) -> str:
    return MOCK_LLM_RESPONSE


class TestBuildPrompt:
    def test_contains_input_text(self):
        prompt = build_extraction_prompt(SAMPLE_LOG)
        assert SAMPLE_LOG in prompt

    def test_returns_string(self):
        assert isinstance(build_extraction_prompt("hello"), str)


class TestParseLlmResponse:
    def test_parses_valid_json(self):
        facts = parse_llm_response(MOCK_LLM_RESPONSE)
        assert len(facts) == 2
        assert all(isinstance(f, Fact) for f in facts)

    def test_handles_wrapped_response(self):
        wrapped = json.dumps({"facts": json.loads(MOCK_LLM_RESPONSE)})
        facts = parse_llm_response(wrapped)
        assert len(facts) == 2


class TestExtractFacts:
    def test_returns_facts(self):
        facts = extract_facts(SAMPLE_LOG, mock_llm)
        assert len(facts) == 2
        assert facts[0].subject == "Chief Engineer Vasquez"

    def test_facts_are_valid_models(self):
        facts = extract_facts(SAMPLE_LOG, mock_llm)
        for fact in facts:
            assert 0.0 <= fact.confidence <= 1.0
            assert fact.source_text


class TestValidateFacts:
    def test_filters_low_confidence(self):
        facts = [
            Fact(subject="A", predicate="did", object="X", source_text="s", confidence=0.9),
            Fact(subject="B", predicate="did", object="Y", source_text="s", confidence=0.5),
        ]
        result = validate_facts(facts, min_confidence=0.7)
        assert len(result) == 1
        assert result[0].subject == "A"

    def test_deduplicates_keeping_highest_confidence(self):
        facts = [
            Fact(subject="A", predicate="did", object="X", source_text="s1", confidence=0.8),
            Fact(subject="A", predicate="did", object="X", source_text="s2", confidence=0.95),
        ]
        result = validate_facts(facts)
        assert len(result) == 1
        assert result[0].confidence == 0.95

    def test_empty_input(self):
        assert validate_facts([]) == []
