"""Demo 03 — Multi-source retrieval orchestration.

Fan out a query to multiple retrieval backends, merge and
deduplicate results, then rank by combined relevance.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    content: str
    source_backend: str
    source_id: str
    score: float
    metadata: dict[str, str] = field(default_factory=dict)


def vector_search(query: str) -> list[SearchResult]:
    return [
        SearchResult("Thruster maintenance protocol v3", "vector", "doc_101", 0.88),
        SearchResult("Engine room safety procedures", "vector", "doc_202", 0.72),
    ]


def graph_search(query: str) -> list[SearchResult]:
    return [
        SearchResult("Vasquez --[repaired]--> thruster array", "graph", "rel_15", 0.91),
        SearchResult("Thruster array --[located_in]--> engine room", "graph", "rel_22", 0.65),
    ]


def keyword_search(query: str) -> list[SearchResult]:
    return [
        SearchResult("Log 4417: thruster array offline at 0300", "keyword", "log_4417", 0.80),
    ]


def merge_and_rank(
    result_sets: list[list[SearchResult]],
    dedup_threshold: float = 0.9,
) -> list[SearchResult]:
    all_results: list[SearchResult] = []
    for rs in result_sets:
        all_results.extend(rs)

    seen_ids: set[str] = set()
    unique: list[SearchResult] = []
    for r in all_results:
        if r.source_id not in seen_ids:
            seen_ids.add(r.source_id)
            unique.append(r)

    return sorted(unique, key=lambda r: r.score, reverse=True)


def main() -> None:
    print("=== Multi-Source Retrieval Demo ===\n")
    query = "thruster array repair"
    print(f"Query: {query}\n")

    backends = [
        ("vector", vector_search),
        ("graph", graph_search),
        ("keyword", keyword_search),
    ]

    result_sets = []
    for name, fn in backends:
        results = fn(query)
        print(f"{name}: {len(results)} results")
        result_sets.append(results)

    merged = merge_and_rank(result_sets)
    print(f"\nMerged and ranked: {len(merged)} unique results\n")
    for i, r in enumerate(merged, 1):
        print(f"  {i}. [{r.source_backend}] {r.content} (score: {r.score:.2f})")


if __name__ == "__main__":
    main()
