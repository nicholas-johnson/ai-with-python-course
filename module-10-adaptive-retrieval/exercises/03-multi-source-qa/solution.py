"""Exercise 03 — Multi-Source QA (solution)"""

from __future__ import annotations

import json
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
    return {name: fn(query) for name, fn in backends.items()}


def merge_and_rank(
    result_sets: dict[str, list[SearchResult]],
) -> list[SearchResult]:
    seen: set[str] = set()
    merged: list[SearchResult] = []

    for results in result_sets.values():
        for r in results:
            if r.source_id not in seen:
                seen.add(r.source_id)
                merged.append(r)

    return sorted(merged, key=lambda r: r.score, reverse=True)


def multi_source_qa(
    query: str,
    backends: dict[str, callable],
    llm_call,
) -> Answer:
    result_sets = fan_out(query, backends)
    ranked = merge_and_rank(result_sets)

    if not ranked:
        return Answer(text="Insufficient data.", sources=[], confidence=0.0)

    context = "\n".join(f"[{r.source_id}] {r.content}" for r in ranked[:5])
    prompt = f"Answer using this context:\n{context}\n\nQuestion: {query}"
    raw = llm_call(prompt)
    data = json.loads(raw)

    return Answer(
        text=data["answer"],
        sources=ranked[:5],
        confidence=data.get("confidence", 0.0),
    )
