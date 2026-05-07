"""Exercise 02 — Self-Critique Retrieval (solution)"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievedDoc:
    content: str
    source: str
    relevance_score: float


@dataclass
class CritiqueResult:
    is_sufficient: bool
    avg_relevance: float
    suggestion: str


def critique_results(
    query: str,
    docs: list[RetrievedDoc],
    threshold: float = 0.6,
) -> CritiqueResult:
    if not docs:
        return CritiqueResult(False, 0.0, "No documents — broaden the query")

    avg = sum(d.relevance_score for d in docs) / len(docs)
    if avg >= threshold:
        return CritiqueResult(True, avg, "Quality sufficient")

    return CritiqueResult(False, avg, f"Avg relevance {avg:.2f} below {threshold} — refine query")


def refine_query(query: str, critique: CritiqueResult) -> str:
    return f"{query} (expanded: include related systems and crew)"


def retrieval_loop(
    query: str,
    retrieve_fn,
    max_attempts: int = 3,
    threshold: float = 0.6,
) -> tuple[list[RetrievedDoc], int]:
    current_query = query
    docs: list[RetrievedDoc] = []

    for attempt in range(1, max_attempts + 1):
        docs = retrieve_fn(current_query)
        critique = critique_results(current_query, docs, threshold)

        if critique.is_sufficient:
            return docs, attempt

        current_query = refine_query(current_query, critique)

    return docs, max_attempts
