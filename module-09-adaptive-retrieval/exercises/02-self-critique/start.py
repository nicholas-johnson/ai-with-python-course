"""Exercise 02 — Self-Critique Retrieval

Evaluate retrieval quality and re-query when results are poor.
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
    """Evaluate retrieved documents against a relevance threshold.

    Return is_sufficient=True if average relevance >= threshold.
    """
    # TODO
    raise NotImplementedError


def refine_query(query: str, critique: CritiqueResult) -> str:
    """Produce a refined query based on the critique feedback."""
    # TODO
    raise NotImplementedError


def retrieval_loop(
    query: str,
    retrieve_fn,
    max_attempts: int = 3,
    threshold: float = 0.6,
) -> tuple[list[RetrievedDoc], int]:
    """Retrieve → critique → refine loop.

    Returns (final_docs, attempts_used).
    Stops early when critique passes or max_attempts is reached.
    """
    # TODO
    raise NotImplementedError
