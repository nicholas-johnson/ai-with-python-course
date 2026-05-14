"""Tests for Exercise 3: Grounded QA."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fact_extractor import Fact
from graph_builder import KnowledgeGraph, build_graph


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
    for name in ("start", "solution"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _make_graph() -> KnowledgeGraph:
    """Create a small test graph."""
    facts = [
        Fact(subject="Vasquez", predicate="repaired", object="port thruster",
             source_text="Vasquez repaired the port thruster.", confidence=0.95),
        Fact(subject="Vasquez", predicate="inspected", object="warp core",
             source_text="Vasquez inspected the warp core.", confidence=0.88),
        Fact(subject="Chen", predicate="plotted", object="course correction",
             source_text="Chen plotted a course correction.", confidence=0.92),
        Fact(subject="Okafor", predicate="reported", object="radiation in cargo bay 2",
             source_text="Okafor reported radiation.", confidence=0.90),
    ]
    return build_graph(facts)


def test_retrieve_evidence_finds_facts():
    """retrieve_evidence returns facts for known entities."""
    mod = _import_start()
    graph = _make_graph()

    evidence = mod.retrieve_evidence(graph, ["Vasquez"], max_hops=1)
    assert len(evidence) >= 2
    sources = [e["source"] for e in evidence]
    assert "Vasquez" in sources


def test_retrieve_evidence_empty_for_unknown():
    """retrieve_evidence returns empty for unknown entities."""
    mod = _import_start()
    graph = _make_graph()

    evidence = mod.retrieve_evidence(graph, ["nonexistent"], max_hops=2)
    assert evidence == []


def test_build_grounded_prompt_has_fact_labels():
    """build_grounded_prompt includes [Fact N] labels."""
    mod = _import_start()

    evidence = [
        {"source": "Vasquez", "target": "thruster", "relation": "repaired", "confidence": 0.95},
        {"source": "Chen", "target": "course", "relation": "plotted", "confidence": 0.92},
    ]
    messages = mod.build_grounded_prompt("What did Vasquez do?", evidence)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "[Fact 1]" in messages[1]["content"]
    assert "[Fact 2]" in messages[1]["content"]
    assert "Vasquez" in messages[1]["content"]


def test_grounded_qa_returns_answer():
    """grounded_qa returns a GroundedAnswer with citations."""
    mod = _import_start()
    graph = _make_graph()

    mock_client = MagicMock()

    entity_response = MagicMock()
    entity_response.choices = [MagicMock(message=MagicMock(
        content='{"entities": ["Vasquez"]}'
    ))]

    answer_response = MagicMock()
    answer_response.choices = [MagicMock(message=MagicMock(
        content="Vasquez repaired the port thruster [Fact 1] and inspected the warp core [Fact 2]."
    ))]

    mock_client.chat.completions.create.side_effect = [entity_response, answer_response]

    result = mod.grounded_qa("What did Vasquez do?", graph, mock_client)

    assert isinstance(result, mod.GroundedAnswer)
    assert len(result.answer) > 0
    assert len(result.evidence) > 0


def test_grounded_qa_no_entities():
    """grounded_qa returns low confidence when no entities found."""
    mod = _import_start()
    graph = _make_graph()

    mock_client = MagicMock()
    entity_response = MagicMock()
    entity_response.choices = [MagicMock(message=MagicMock(
        content='{"entities": []}'
    ))]
    mock_client.chat.completions.create.return_value = entity_response

    result = mod.grounded_qa("What is the meaning of life?", graph, mock_client)

    assert result.confidence == 0.0
    assert result.evidence == []
