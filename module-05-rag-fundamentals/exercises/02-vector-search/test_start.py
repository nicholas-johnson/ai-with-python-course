"""Tests for Exercise 02 — Vector Search."""

import pytest

from start import MissionVectorStore


@pytest.mark.skip(reason="Skeleton — implement MissionVectorStore in start.py")
def test_search_returns_ranked_chunks():
    store = MissionVectorStore()
    store.add_documents([{"id": "a", "text": "dock alpha"}])
    hits = store.search("alpha dock", k=1)
    assert len(hits) == 1
