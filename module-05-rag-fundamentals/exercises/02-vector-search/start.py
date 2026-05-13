"""
Exercise 02 — Vector Search
Embed and search mission archives (local-first).
"""

from __future__ import annotations

from typing import Any


# TODO: Implement MissionVectorStore with embed(text: str) -> list[float] (or use a stub)
# TODO: add_documents(chunks: list[dict]) — each dict has at least "text" and "id"
# TODO: search(query: str, k: int = 5) -> list[dict] with keys: id, text, score


class MissionVectorStore:
    """Minimal vector store for mission archive chunks."""

    def __init__(self) -> None:
        pass

    def add_documents(self, chunks: list[dict[str, Any]]) -> None:
        raise NotImplementedError("TODO")

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError("TODO")
