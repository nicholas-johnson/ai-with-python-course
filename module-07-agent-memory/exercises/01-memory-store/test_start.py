"""Tests for Exercise 01 — Memory Store.

No API key and no ChromaDB: the collection is a dict-backed stub that returns
canned distances, and embeddings come from a MagicMock.
"""

import importlib
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

DAY = 86_400


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


def _matches(metadata: dict, where: dict | None) -> bool:
    """Evaluate the {"$and": [{"field": {"$eq": value}}, ...]} filter form."""
    if not where:
        return True
    for clause in where.get("$and", [where]):
        for field, condition in clause.items():
            if metadata.get(field) != condition["$eq"]:
                return False
    return True


class FakeCollection:
    """Stands in for a Chroma collection.

    Distances are canned per document text, so ranking is deterministic
    without embedding anything.
    """

    def __init__(self, distances: dict[str, float] | None = None):
        self.rows: dict[str, dict] = {}
        self.distances = distances or {}

    def add(self, ids, embeddings, documents, metadatas):
        for memory_id, document, metadata in zip(ids, documents, metadatas):
            self.rows[memory_id] = {"document": document, "metadata": dict(metadata)}

    def query(self, query_embeddings, n_results, where=None):
        hits = [
            (memory_id, row)
            for memory_id, row in self.rows.items()
            if _matches(row["metadata"], where)
        ][:n_results]
        return {
            "ids": [[memory_id for memory_id, _ in hits]],
            "documents": [[row["document"] for _, row in hits]],
            "metadatas": [[row["metadata"] for _, row in hits]],
            "distances": [[self.distances.get(row["document"], 0.5) for _, row in hits]],
        }

    def get(self, ids=None, where=None):
        if ids is not None:
            hits = [(i, self.rows[i]) for i in ids if i in self.rows]
        else:
            hits = [
                (memory_id, row)
                for memory_id, row in self.rows.items()
                if _matches(row["metadata"], where)
            ]
        return {
            "ids": [memory_id for memory_id, _ in hits],
            "documents": [row["document"] for _, row in hits],
            "metadatas": [row["metadata"] for _, row in hits],
        }

    def update(self, ids, metadatas):
        for memory_id, metadata in zip(ids, metadatas):
            self.rows[memory_id]["metadata"] = dict(metadata)


@pytest.fixture()
def client():
    """A stand-in OpenAI client that returns a fixed embedding."""
    mock = MagicMock()
    mock.embeddings.create.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
    return mock


def test_normalise_spreads_across_unit_range():
    """normalise maps the best candidate to 1.0 and the worst to 0.0."""
    mod = _import_start()
    result = mod.normalise([0.10, 0.20, 0.30])
    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(1.0)
    assert 0.0 < result[1] < 1.0


def test_normalise_handles_edge_cases():
    """An empty list stays empty; identical similarities all score 1.0."""
    mod = _import_start()
    assert mod.normalise([]) == []
    assert mod.normalise([0.4, 0.4]) == [1.0, 1.0]


def test_recency_weight_halves_each_half_life():
    """A memory one half-life old counts for half as much."""
    mod = _import_start()
    now = time.time()
    assert mod.recency_weight(now, now) == pytest.approx(1.0)
    one_half_life = now - mod.HALF_LIFE_DAYS * DAY
    assert mod.recency_weight(one_half_life, now) == pytest.approx(0.5, abs=1e-6)
    two_half_lives = now - 2 * mod.HALF_LIFE_DAYS * DAY
    assert mod.recency_weight(two_half_lives, now) == pytest.approx(0.25, abs=1e-6)


def test_score_memory_combines_three_signals():
    """The score is the weighted sum of relevance, recency, and importance."""
    mod = _import_start()
    now = time.time()
    recency, score = mod.score_memory(1.0, now, 1.0, now)
    assert recency == pytest.approx(1.0)
    assert score == pytest.approx(
        mod.RELEVANCE_WEIGHT + mod.RECENCY_WEIGHT + mod.IMPORTANCE_WEIGHT
    )

    # Perfectly relevant but ancient and unimportant: relevance only.
    ancient = now - 3000 * DAY
    _, weak = mod.score_memory(1.0, ancient, 0.0, now)
    assert weak == pytest.approx(mod.RELEVANCE_WEIGHT, abs=1e-3)
    assert weak < score


def test_remember_then_recall_round_trip(client):
    """A written memory comes back from recall with its metadata intact."""
    mod = _import_start()
    store = mod.MemoryStore(client, FakeCollection())

    memory_id = store.remember(
        "Zara takes the Comet Tail with extra fizz.",
        patron="zara",
        kind="preference",
        importance=0.9,
    )
    assert isinstance(memory_id, str) and memory_id

    results = store.recall("usual drink", patron="zara", k=5)
    assert len(results) == 1
    assert results[0].text == "Zara takes the Comet Tail with extra fizz."
    assert results[0].kind == "preference"
    assert results[0].importance == pytest.approx(0.9)


def test_recall_namespaces_by_patron(client):
    """One patron's memories never surface for another."""
    mod = _import_start()
    store = mod.MemoryStore(client, FakeCollection())

    store.remember("Zara is the quartermaster on the Pathfinder.", patron="zara")
    store.remember("Tanaka cannot have synthcitrus.", patron="tanaka")

    zara = store.recall("who is this", patron="zara", k=5)
    tanaka = store.recall("who is this", patron="tanaka", k=5)

    assert [m.text for m in zara] == ["Zara is the quartermaster on the Pathfinder."]
    assert [m.text for m in tanaka] == ["Tanaka cannot have synthcitrus."]


def test_recall_ranks_relevance_above_recency(client):
    """A relevant old memory beats a fresh irrelevant one."""
    mod = _import_start()
    relevant = "Zara reacts badly to synthcitrus in any form."
    recent = "Zara's shore leave ends on stardate 2288.4."
    collection = FakeCollection(distances={relevant: 0.6, recent: 0.95})
    store = mod.MemoryStore(client, collection)

    now = time.time()
    store.remember(relevant, patron="zara", importance=1.0, written_at=now - 210 * DAY)
    store.remember(recent, patron="zara", importance=0.4, written_at=now - 1 * DAY)

    results = store.recall("something citrus-forward", patron="zara", k=2)
    assert results[0].text == relevant, "Relevance and importance should outweigh recency"
    assert results[0].recency < 0.05, "The winning memory really is old"


def test_recall_respects_k(client):
    """recall returns at most k memories."""
    mod = _import_start()
    store = mod.MemoryStore(client, FakeCollection())
    for index in range(6):
        store.remember(f"Fact number {index} about Zara.", patron="zara")

    assert len(store.recall("anything", patron="zara", k=3)) == 3


def test_forget_is_a_soft_delete(client):
    """forget stops recall without removing the row."""
    mod = _import_start()
    collection = FakeCollection()
    store = mod.MemoryStore(client, collection)

    memory_id = store.remember("Zara mentioned the cargo in bay four.", patron="zara")
    assert store.forget(memory_id) is True

    assert store.recall("cargo", patron="zara", k=5) == []
    assert store.all_active(patron="zara") == []
    assert memory_id in collection.rows, "The row must survive for the audit trail"
    assert collection.rows[memory_id]["metadata"]["active"] is False


def test_forget_unknown_id_returns_false(client):
    mod = _import_start()
    store = mod.MemoryStore(client, FakeCollection())
    assert store.forget("not-a-real-id") is False


def test_supersede_records_the_replacement(client):
    """supersede retires the old memory and records what replaced it."""
    mod = _import_start()
    collection = FakeCollection()
    store = mod.MemoryStore(client, collection)

    old = store.remember("Zara prefers her briefings short.", patron="zara")
    new = store.remember("Zara wants the full detail on everything.", patron="zara")
    assert store.supersede(old, by=new) is True

    live = [m.text for m in store.recall("briefings", patron="zara", k=5)]
    assert live == ["Zara wants the full detail on everything."]
    assert collection.rows[old]["metadata"]["superseded_by"] == new


def test_build_system_prompt_includes_memories():
    """The prompt carries the persona and the recalled memory text."""
    mod = _import_start()
    memory = mod.ScoredMemory(
        memory_id="m1",
        text="Zara takes the Comet Tail with extra fizz.",
        kind="preference",
        importance=0.9,
        written_at=time.time(),
        relevance=1.0,
        recency=1.0,
        score=0.95,
    )

    prompt = mod.build_system_prompt([memory])
    assert "BARKEEP" in prompt
    assert "Comet Tail" in prompt

    empty = mod.build_system_prompt([])
    assert "BARKEEP" in empty
    assert "Comet Tail" not in empty
