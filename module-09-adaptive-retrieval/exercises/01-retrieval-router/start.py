"""Exercise 01 — Retrieval Router

Classify queries and dispatch to the right retrieval backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RetrievalBackend(Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    KEYWORD = "keyword"


@dataclass
class RoutingDecision:
    backend: RetrievalBackend
    confidence: float
    reasoning: str


def classify_query(query: str) -> RoutingDecision:
    """Classify a query and choose the best retrieval backend.

    - Relationship queries → GRAPH
    - Exact-match queries → KEYWORD
    - Everything else → VECTOR
    """
    # TODO
    raise NotImplementedError


def route_and_retrieve(
    query: str,
    backends: dict[RetrievalBackend, callable],
) -> list[dict]:
    """Classify the query, call the matching backend, return results.

    Each backend callable accepts a query string and returns list[dict].
    """
    # TODO
    raise NotImplementedError
