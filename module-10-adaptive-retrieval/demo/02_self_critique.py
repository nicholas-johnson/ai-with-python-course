"""Demo 02 — Self-critique retrieval loop.

Demonstrates corrective RAG: retrieve documents, evaluate their
relevance, and re-query with refined terms if quality is too low.
"""

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
        return CritiqueResult(False, 0.0, "No documents retrieved — broaden the query")

    avg = sum(d.relevance_score for d in docs) / len(docs)
    if avg >= threshold:
        return CritiqueResult(True, avg, "Results look good — proceed to answer")

    return CritiqueResult(
        False, avg,
        f"Average relevance {avg:.2f} below threshold {threshold} — refine query terms",
    )


def refine_query(original: str, critique: CritiqueResult) -> str:
    return f"{original} (expanded: include related systems and crew)"


def retrieval_loop(
    query: str,
    retrieve_fn,
    max_attempts: int = 3,
    threshold: float = 0.6,
) -> tuple[list[RetrievedDoc], int]:
    current_query = query
    for attempt in range(1, max_attempts + 1):
        docs = retrieve_fn(current_query)
        critique = critique_results(current_query, docs, threshold)
        print(f"  Attempt {attempt}: {len(docs)} docs, avg relevance {critique.avg_relevance:.2f}")
        print(f"    → {critique.suggestion}")

        if critique.is_sufficient:
            return docs, attempt
        current_query = refine_query(current_query, critique)

    return docs, max_attempts


def mock_retrieve(query: str) -> list[RetrievedDoc]:
    boost = 0.15 if "expanded" in query else 0.0
    return [
        RetrievedDoc("Thruster repair log entry", "log_2287", 0.45 + boost),
        RetrievedDoc("Vasquez maintenance schedule", "crew_db", 0.55 + boost),
        RetrievedDoc("Port array specifications", "tech_manual", 0.50 + boost),
    ]


def main() -> None:
    print("=== Self-Critique Retrieval Demo ===\n")
    query = "thruster array repair details"
    print(f"Query: {query}\n")
    docs, attempts = retrieval_loop(query, mock_retrieve, threshold=0.6)
    print(f"\nCompleted in {attempts} attempt(s), returning {len(docs)} docs")


if __name__ == "__main__":
    main()
