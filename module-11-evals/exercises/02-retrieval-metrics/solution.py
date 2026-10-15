"""
Exercise 02 — Retrieval Metrics (Solution)

Score ranked retrieval against a labelled query set.
"""

from __future__ import annotations

import json
from pathlib import Path


def recall_at_k(ranked_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top = set(ranked_ids[:k])
    relevant = set(relevant_ids)
    return len(top & relevant) / len(relevant)


def precision_at_k(ranked_ids: list[str], relevant_ids: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = set(ranked_ids[:k])
    relevant = set(relevant_ids)
    return len(top & relevant) / k


def mrr(ranked_ids: list[str], relevant_ids: list[str]) -> float:
    relevant = set(relevant_ids)
    for rank, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def evaluate_queries(queries: list[dict], k: int) -> list[dict]:
    results = []
    for query in queries:
        ranked = query["ranked_ids"]
        relevant = query["relevant_ids"]
        results.append(
            {
                **query,
                "recall": recall_at_k(ranked, relevant, k),
                "precision": precision_at_k(ranked, relevant, k),
                "mrr": mrr(ranked, relevant),
            }
        )
    return results


def summarize(evaluations: list[dict]) -> dict:
    n = len(evaluations)
    if n == 0:
        return {
            "avg_recall": 0.0,
            "avg_precision": 0.0,
            "avg_mrr": 0.0,
            "num_queries": 0,
        }
    return {
        "avg_recall": sum(e["recall"] for e in evaluations) / n,
        "avg_precision": sum(e["precision"] for e in evaluations) / n,
        "avg_mrr": sum(e["mrr"] for e in evaluations) / n,
        "num_queries": n,
    }


def attach_labels(ranked_run: list[dict], labeled: list[dict]) -> list[dict]:
    gold = {row["query"]: row["relevant_ids"] for row in labeled}
    return [
        {
            "query": row["query"],
            "ranked_ids": row["ranked_ids"],
            "relevant_ids": gold[row["query"]],
        }
        for row in ranked_run
    ]


if __name__ == "__main__":
    here = Path(__file__).parent / "data"
    labeled = json.loads((here / "labeled_queries.json").read_text())
    runs = json.loads((here / "ranked_runs.json").read_text())
    k = 3
    print(f"Retrieval metrics @k={k}\n")
    for name, run in runs.items():
        queries = attach_labels(run, labeled)
        summary = summarize(evaluate_queries(queries, k=k))
        print(
            f"  {name:10}  recall={summary['avg_recall']:.2f}  "
            f"precision={summary['avg_precision']:.2f}  "
            f"mrr={summary['avg_mrr']:.2f}  n={summary['num_queries']}"
        )
