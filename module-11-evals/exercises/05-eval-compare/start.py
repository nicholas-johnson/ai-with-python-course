"""
Exercise 05 — Eval Compare

Combine retrieval, judge, and faithfulness numbers into a scorecard,
pick a winning config, and gate a release against floors.
"""

from __future__ import annotations

import json
from pathlib import Path

# overall = 0.35 * recall + 0.35 * judge_norm + 0.30 * faithfulness
# judge_norm = (correctness + completeness + relevance) / 15  → 0..1
RECALL_WEIGHT = 0.35
JUDGE_WEIGHT = 0.35
FAITH_WEIGHT = 0.30


def overall_score(retrieval: dict, judge: dict, faithfulness: dict) -> float:
    """
    Weighted overall score in [0, 1].

    overall = 0.35 * avg_recall
            + 0.35 * (avg_correctness + avg_completeness + avg_relevance) / 15
            + 0.30 * avg_faithfulness

    TODO: implement the formula above
    """
    # TODO: implement
    pass


def build_scorecard(
    config_name: str,
    retrieval: dict,
    judge: dict,
    faithfulness: dict,
) -> dict:
    """
    One scorecard per config.

    Args:
        config_name: e.g. "rag" or "rag_rerank"
        retrieval: {avg_recall, avg_precision, avg_mrr}
        judge: {avg_correctness, avg_completeness, avg_relevance}
        faithfulness: {avg_faithfulness}

    Returns:
        {
            "config": str,
            "retrieval": dict,       # as passed in
            "judge": dict,
            "faithfulness": dict,
            "overall": float,
        }

    TODO: call overall_score and assemble the dict
    """
    # TODO: implement
    pass


def metric_value(scorecard: dict, metric: str) -> float:
    """
    Look up a metric on a scorecard.

    Supported names:
      - "overall"
      - retrieval: "avg_recall", "avg_precision", "avg_mrr"
      - judge: "avg_correctness", "avg_completeness", "avg_relevance"
      - faithfulness: "avg_faithfulness"

    TODO: map metric name to the nested value
    """
    # TODO: implement
    pass


def compare_configs(scorecards: list[dict], metric: str = "overall") -> dict:
    """
    Rank configs by `metric` (highest wins).

    Returns:
        {
            "metric": str,
            "winner": str,          # config name
            "ranking": [{"config": str, "value": float}, ...],  # high to low
        }

    If scorecards is empty, winner is None and ranking is [].

    TODO: sort by metric_value descending
    """
    # TODO: implement
    pass


def gate(scorecard: dict, thresholds: dict) -> dict:
    """
    Fail if any named metric is strictly below its floor.

    `thresholds` keys are the same names as metric_value().

    Returns:
        {
            "passed": bool,
            "failures": [{"metric": str, "value": float, "threshold": float}, ...],
        }

    TODO: compare each threshold; passed iff failures is empty
    """
    # TODO: implement
    pass


if __name__ == "__main__":
    data = json.loads((Path(__file__).parent / "data" / "config_runs.json").read_text())
    scorecards = [
        build_scorecard(name, run["retrieval"], run["judge"], run["faithfulness"])
        for name, run in data.items()
    ]
    print("Scorecards\n")
    if any(s is None for s in scorecards):
        print("  not implemented")
    else:
        for card in scorecards:
            print(
                f"  {card['config']:12}  overall={card['overall']:.3f}  "
                f"recall={card['retrieval']['avg_recall']:.2f}  "
                f"faithfulness={card['faithfulness']['avg_faithfulness']:.2f}"
            )
        comparison = compare_configs(scorecards, metric="overall")
        print(f"\n  winner ({comparison['metric']}): {comparison['winner']}")
        floors = {"avg_recall": 0.6, "avg_faithfulness": 0.75, "overall": 0.55}
        print("\nRelease gate", floors)
        for card in scorecards:
            result = gate(card, floors)
            mark = "PASS" if result["passed"] else "FAIL"
            print(f"  [{mark}] {card['config']}")
            for fail in result["failures"]:
                print(
                    f"         {fail['metric']}: {fail['value']:.3f} < {fail['threshold']}"
                )
