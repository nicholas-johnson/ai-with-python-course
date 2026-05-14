"""Tests for Exercise 1: Build the Index."""

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


def test_chunk_text_basic():
    """chunk_text splits text into overlapping windows."""
    mod = _import_start()
    text = "A" * 100
    chunks = mod.chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"
    assert all(len(c) <= 40 for c in chunks), "All chunks should be <= chunk_size"


def test_chunk_text_overlap():
    """Consecutive chunks share overlap characters."""
    mod = _import_start()
    text = "abcdefghijklmnopqrstuvwxyz" * 4  # 104 chars
    chunks = mod.chunk_text(text, chunk_size=30, overlap=10)
    for i in range(len(chunks) - 1):
        tail = chunks[i][-10:]
        head = chunks[i + 1][:10]
        assert tail == head, f"Chunk {i} tail should overlap with chunk {i+1} head"


def test_chunk_text_short():
    """Short text produces a single chunk."""
    mod = _import_start()
    chunks = mod.chunk_text("hello", chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == "hello"


@patch("openai.OpenAI")
def test_build_index_creates_collection(mock_openai_cls):
    """build_index returns a ChromaDB collection with chunks."""
    mod = _import_start()

    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    fake_embedding = [0.1] * 1536
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_embedding)]
    mock_client.embeddings.create.return_value = mock_response

    sample_logs = [
        {
            "id": "LOG-001",
            "content": "Test log content that is long enough to produce at least one chunk for indexing.",
            "author": "Test Author",
            "category": "test",
            "tags": ["test"],
        }
    ]

    if hasattr(mod, "client"):
        original_client = mod.client
        mod.client = mock_client

    try:
        collection = mod.build_index(sample_logs)
        assert collection.count() > 0, "Collection should have chunks"
    finally:
        if hasattr(mod, "client"):
            mod.client = original_client


def test_search_returns_results():
    """search returns a list of result dicts with expected keys."""
    mod = _import_start()

    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["chunk_0", "chunk_1"]],
        "documents": [["text 0", "text 1"]],
        "distances": [[0.1, 0.3]],
        "metadatas": [[{"source_id": "LOG-001"}, {"source_id": "LOG-002"}]],
    }

    with patch.object(mod, "client", create=True) as mock_client:
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response

        results = mod.search(mock_collection, "test query", k=2)

    assert len(results) == 2
    assert "id" in results[0]
    assert "text" in results[0]
    assert "distance" in results[0]
    assert "metadata" in results[0]
