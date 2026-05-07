"""Exercise 03 — Multi-Source QA

Fan out to multiple retrieval backends, merge results, answer with citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    content: str
    source_backend: str
    source_id: str
    score: float


@dataclass
class Answer:
    text: str
    sources: list[SearchResult]
    confidence: float


def fan_out(
    query: str,
    backends: dict[str, callable],
) -> dict[str, list[SearchResult]]:
    """Query every backend and return results keyed by backend name."""
    # TODO
    raise NotImplementedError


def merge_and_rank(
    result_sets: dict[str, list[SearchResult]],
) -> list[SearchResult]:
    """Merge all result sets, deduplicate by source_id, sort by score descending."""
    # TODO
    raise NotImplementedError


def multi_source_qa(
    query: str,
    backends: dict[str, callable],
    llm_call,
) -> Answer:
    """End-to-end: fan out, merge, build prompt, call LLM, return Answer.

    If no results, return Answer with confidence=0.0.
    """
    # TODO
    raise NotImplementedError
