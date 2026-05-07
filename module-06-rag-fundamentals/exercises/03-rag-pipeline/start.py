"""
Exercise 03 — RAG Pipeline
End-to-end retrieval + grounded response with citation linking.
"""

from __future__ import annotations

from typing import Any, Protocol


class Retriever(Protocol):
    def search(self, query: str, k: int) -> list[dict[str, Any]]: ...


# TODO: Implement run_rag(query: str, retriever: Retriever, k: int) -> dict
# Return at least: {"answer": str, "citations": list[str]}  # citation = chunk ids used


def run_rag(query: str, retriever: Retriever, k: int = 4) -> dict[str, Any]:
    raise NotImplementedError("TODO: retrieve, build prompt, return answer + citations")
