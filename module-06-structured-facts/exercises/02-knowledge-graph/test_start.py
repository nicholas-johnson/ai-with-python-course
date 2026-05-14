"""Tests for Exercise 2: Knowledge Graph."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock


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


def _make_fact(subject, predicate, obj, confidence=0.9):
    """Create a Fact-like object for testing."""
    from fact_extractor import Fact
    return Fact(
        subject=subject,
        predicate=predicate,
        object=obj,
        source_text=f"{subject} {predicate} {obj}.",
        confidence=confidence,
    )


def test_add_fact_creates_nodes_and_edge():
    """add_fact should create subject and object nodes plus an edge."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    fact = _make_fact("Vasquez", "repaired", "thruster")
    kg.add_fact(fact)

    assert "Vasquez" in kg.graph.nodes
    assert "thruster" in kg.graph.nodes
    assert kg.graph.has_edge("Vasquez", "thruster")


def test_neighbours_returns_connections():
    """neighbours should return all edges for an entity."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    kg.add_fact(_make_fact("Vasquez", "repaired", "thruster"))
    kg.add_fact(_make_fact("Vasquez", "inspected", "warp core"))

    edges = kg.neighbours("Vasquez")
    assert len(edges) >= 2


def test_neighbours_empty_for_unknown():
    """neighbours returns empty list for unknown entity."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    assert kg.neighbours("nonexistent") == []


def test_find_path_direct():
    """find_path finds a direct connection."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    kg.add_fact(_make_fact("A", "connects", "B"))

    path = kg.find_path("A", "B")
    assert path == ["A", "B"]


def test_find_path_multi_hop():
    """find_path finds a multi-hop path."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    kg.add_fact(_make_fact("A", "connects", "B"))
    kg.add_fact(_make_fact("B", "connects", "C"))

    path = kg.find_path("A", "C")
    assert path == ["A", "B", "C"]


def test_find_path_no_connection():
    """find_path returns None when no path exists."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    kg.add_fact(_make_fact("A", "connects", "B"))
    kg.add_fact(_make_fact("C", "connects", "D"))

    path = kg.find_path("A", "D")
    assert path is None


def test_build_graph():
    """build_graph creates a populated graph from facts."""
    mod = _import_start()
    facts = [
        _make_fact("Vasquez", "repaired", "thruster"),
        _make_fact("Chen", "plotted", "course correction"),
        _make_fact("Okafor", "reported", "radiation"),
    ]
    kg = mod.build_graph(facts)

    assert kg.graph.number_of_nodes() == 6
    assert kg.graph.number_of_edges() == 3


def test_find_connections_within_hops():
    """find_connections returns edges within max_hops."""
    mod = _import_start()
    kg = mod.KnowledgeGraph()
    kg.add_fact(_make_fact("A", "r1", "B"))
    kg.add_fact(_make_fact("B", "r2", "C"))
    kg.add_fact(_make_fact("C", "r3", "D"))

    edges = kg.find_connections("A", max_hops=2)
    edge_pairs = [(s, t) for s, t, _, _ in edges]
    assert ("A", "B") in edge_pairs
    assert ("B", "C") in edge_pairs
