"""Demo 01 — Retrieval routing.

Classifies incoming queries by intent and dispatches them to the
appropriate retrieval backend: vector search for semantic similarity,
graph lookup for entity relationships, or keyword search for exact terms.
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


ROUTING_RULES = {
    "relationship": RetrievalBackend.GRAPH,
    "who": RetrievalBackend.GRAPH,
    "connected": RetrievalBackend.GRAPH,
    "exact": RetrievalBackend.KEYWORD,
    "error code": RetrievalBackend.KEYWORD,
    "log entry": RetrievalBackend.KEYWORD,
}


def classify_query(query: str) -> RoutingDecision:
    query_lower = query.lower()

    for keyword, backend in ROUTING_RULES.items():
        if keyword in query_lower:
            return RoutingDecision(
                backend=backend,
                confidence=0.85,
                reasoning=f"Matched keyword '{keyword}' → {backend.value}",
            )

    return RoutingDecision(
        backend=RetrievalBackend.VECTOR,
        confidence=0.7,
        reasoning="No keyword match — defaulting to semantic vector search",
    )


SAMPLE_QUERIES = [
    "What is the relationship between Vasquez and the thruster array?",
    "Find the exact error code from sensor log 4417",
    "How does the Pathfinder handle radiation shielding?",
    "Who reported the cargo bay incident?",
]


def main() -> None:
    print("=== Retrieval Routing Demo ===\n")
    for query in SAMPLE_QUERIES:
        decision = classify_query(query)
        print(f"Q: {query}")
        print(f"   → {decision.backend.value} (confidence {decision.confidence:.0%})")
        print(f"     {decision.reasoning}\n")


if __name__ == "__main__":
    main()
