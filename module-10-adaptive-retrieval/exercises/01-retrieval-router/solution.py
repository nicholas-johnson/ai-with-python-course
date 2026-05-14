"""Exercise 01 — Retrieval Router (solution)"""

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


GRAPH_KEYWORDS = ["relationship", "connected", "who", "between"]
KEYWORD_KEYWORDS = ["error code", "log entry", "serial number", "exact"]


def classify_query(query: str) -> RoutingDecision:
    query_lower = query.lower()

    for kw in GRAPH_KEYWORDS:
        if kw in query_lower:
            return RoutingDecision(
                RetrievalBackend.GRAPH, 0.85,
                f"Matched graph keyword '{kw}'",
            )

    for kw in KEYWORD_KEYWORDS:
        if kw in query_lower:
            return RoutingDecision(
                RetrievalBackend.KEYWORD, 0.85,
                f"Matched keyword pattern '{kw}'",
            )

    return RoutingDecision(
        RetrievalBackend.VECTOR, 0.7,
        "No specific pattern matched — using semantic search",
    )


def route_and_retrieve(
    query: str,
    backends: dict[RetrievalBackend, callable],
) -> list[dict]:
    decision = classify_query(query)
    retrieve_fn = backends[decision.backend]
    return retrieve_fn(query)
