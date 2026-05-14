"""Tests for Exercise 1: Fact Extractor."""

import json
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


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


MOCK_FACTS_JSON = json.dumps({
    "facts": [
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
        {
            "subject": "Navigation Officer Chen",
            "predicate": "plotted",
            "object": "course correction",
            "source_text": "Navigation Officer Chen plotted a course correction.",
            "confidence": 0.50,
        },
    ]
})


def test_fact_model_validates():
    """Fact model accepts valid data and rejects invalid."""
    mod = _import_start()
    fact = mod.Fact(
        subject="Vasquez",
        predicate="repaired",
        object="thruster",
        source_text="Vasquez repaired thruster.",
        confidence=0.9,
    )
    assert fact.subject == "Vasquez"
    assert 0.0 <= fact.confidence <= 1.0


def test_fact_model_rejects_bad_confidence():
    """Fact model rejects confidence outside 0-1."""
    mod = _import_start()
    import pytest
    with pytest.raises(Exception):
        mod.Fact(
            subject="A", predicate="did", object="B",
            source_text="s", confidence=1.5,
        )


def test_extract_facts_returns_facts():
    """extract_facts returns a list of Fact objects."""
    mod = _import_start()

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=MOCK_FACTS_JSON))]
    mock_client.chat.completions.create.return_value = mock_response

    result = mod.extract_facts("Some ship log text.", mock_client)
    if isinstance(result, tuple):
        facts = result[0]
    else:
        facts = result

    assert len(facts) >= 2
    assert all(isinstance(f, mod.Fact) for f in facts)


def test_validate_facts_filters_low_confidence():
    """validate_facts removes facts below the threshold."""
    mod = _import_start()
    facts = [
        mod.Fact(subject="A", predicate="did", object="X", source_text="s", confidence=0.9),
        mod.Fact(subject="B", predicate="did", object="Y", source_text="s", confidence=0.5),
        mod.Fact(subject="C", predicate="did", object="Z", source_text="s", confidence=0.3),
    ]
    result = mod.validate_facts(facts, min_confidence=0.7)
    assert len(result) == 1
    assert result[0].subject == "A"


def test_validate_facts_deduplicates():
    """validate_facts keeps only the highest-confidence duplicate."""
    mod = _import_start()
    facts = [
        mod.Fact(subject="A", predicate="did", object="X", source_text="s1", confidence=0.8),
        mod.Fact(subject="A", predicate="did", object="X", source_text="s2", confidence=0.95),
        mod.Fact(subject="A", predicate="did", object="X", source_text="s3", confidence=0.75),
    ]
    result = mod.validate_facts(facts)
    assert len(result) == 1
    assert result[0].confidence == 0.95


def test_validate_facts_empty():
    """validate_facts returns empty list for empty input."""
    mod = _import_start()
    assert mod.validate_facts([]) == []
