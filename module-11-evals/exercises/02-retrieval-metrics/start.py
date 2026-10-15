"""
Exercise 02 — Retrieval Metrics

Score ranked retrieval against a labelled query set.
Pure Python — no embeddings, no API key.
"""

from __future__ import annotations

import json
from pathlib import Path


def recall_at_k(ranked_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """
    Fraction of relevant documents that appear in the top k results.

    recall@k = |top_k ∩ relevant| / |relevant|

    Return 0.0 if relevant_ids is empty. Use ranked_ids[:k] as the retrieved set.

    TODO: implement recall@k
    """
    # TODO: implement
    pass


def precision_at_k(ranked_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """
    Fraction of the top k results that are relevant.

    precision@k = |top_k ∩ relevant| / k

    Return 0.0 if k is 0. Always divide by k (not by len(top_k)), so returning
    fewer than k hits is penalised.

    TODO: implement precision@k
    """
    # TODO: implement
    pass


def mrr(ranked_ids: list[str], relevant_ids: list[str]) -> float:
    """
    Mean Reciprocal Rank for a *single* query: 1 / rank of the first relevant
    document (1-based). Return 0.0 if no relevant document appears.

    TODO: implement MRR
    """
    # TODO: implement
    pass


def evaluate_queries(queries: list[dict], k: int) -> list[dict]:
    """
    Score each query.

    Each query dict has:
      - "query": str
      - "ranked_ids": list[str]
      - "relevant_ids": list[str]

    Return the same dicts with extra keys:
      - "recall": float   (recall@k)
      - "precision": float  (precision@k)
      - "mrr": float

    TODO: call the three metric functions per query
    """
    # TODO: implement
    pass


def summarize(evaluations: list[dict]) -> dict:
    """
    Average metrics across evaluate_queries output.

    Returns:
        {
            "avg_recall": float,
            "avg_precision": float,
            "avg_mrr": float,
            "num_queries": int,
        }

    Return zeros if evaluations is empty.

    TODO: implement averages
    """
    # TODO: implement
    pass


def attach_labels(ranked_run: list[dict], labeled: list[dict]) -> list[dict]:
    """Join a ranked run to gold relevant_ids by query string. Provided."""
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
        if summary is None:
            print(f"  {name}: not implemented")
            continue
        print(
            f"  {name:10}  recall={summary['avg_recall']:.2f}  "
            f"precision={summary['avg_precision']:.2f}  "
            f"mrr={summary['avg_mrr']:.2f}  n={summary['num_queries']}"
        )
