"""
Exercise 05 — Eval Compare (Solution)

Combine retrieval, judge, and faithfulness numbers into a scorecard,
pick a winning config, and gate a release against floors.
"""

from __future__ import annotations

import json
from pathlib import Path

RECALL_WEIGHT = 0.35
JUDGE_WEIGHT = 0.35
FAITH_WEIGHT = 0.30

_RETRIEVAL_KEYS = {"avg_recall", "avg_precision", "avg_mrr"}
_JUDGE_KEYS = {"avg_correctness", "avg_completeness", "avg_relevance"}
_FAITH_KEYS = {"avg_faithfulness"}


def overall_score(retrieval: dict, judge: dict, faithfulness: dict) -> float:
    judge_norm = (
        judge["avg_correctness"] + judge["avg_completeness"] + judge["avg_relevance"]
    ) / 15.0
    return (
        RECALL_WEIGHT * retrieval["avg_recall"]
        + JUDGE_WEIGHT * judge_norm
        + FAITH_WEIGHT * faithfulness["avg_faithfulness"]
    )


def build_scorecard(
    config_name: str,
    retrieval: dict,
    judge: dict,
    faithfulness: dict,
) -> dict:
    return {
        "config": config_name,
        "retrieval": retrieval,
        "judge": judge,
        "faithfulness": faithfulness,
        "overall": overall_score(retrieval, judge, faithfulness),
    }


def metric_value(scorecard: dict, metric: str) -> float:
    if metric == "overall":
        return scorecard["overall"]
    if metric in _RETRIEVAL_KEYS:
        return scorecard["retrieval"][metric]
    if metric in _JUDGE_KEYS:
        return scorecard["judge"][metric]
    if metric in _FAITH_KEYS:
        return scorecard["faithfulness"][metric]
    raise KeyError(f"Unknown metric: {metric}")


def compare_configs(scorecards: list[dict], metric: str = "overall") -> dict:
    ranking = sorted(
        (
            {"config": card["config"], "value": metric_value(card, metric)}
            for card in scorecards
        ),
        key=lambda row: row["value"],
        reverse=True,
    )
    return {
        "metric": metric,
        "winner": ranking[0]["config"] if ranking else None,
        "ranking": ranking,
    }


def gate(scorecard: dict, thresholds: dict) -> dict:
    failures = []
    for metric, minimum in thresholds.items():
        value = metric_value(scorecard, metric)
        if value < minimum:
            failures.append(
                {"metric": metric, "value": value, "threshold": minimum}
            )
    return {"passed": not failures, "failures": failures}


if __name__ == "__main__":
    data = json.loads((Path(__file__).parent / "data" / "config_runs.json").read_text())
    scorecards = [
        build_scorecard(name, run["retrieval"], run["judge"], run["faithfulness"])
        for name, run in data.items()
    ]
    print("Scorecards\n")
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
            print(f"         {fail['metric']}: {fail['value']:.3f} < {fail['threshold']}")
