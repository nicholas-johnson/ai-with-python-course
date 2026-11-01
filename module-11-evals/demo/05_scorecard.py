"""Part 5: One score, then a floor that fails the weaker pipeline."""


def overall_score(retrieval, judge, faith):
    judge_norm = (
        judge["avg_correctness"] + judge["avg_completeness"] + judge["avg_relevance"]
    ) / 15.0
    return 0.35 * retrieval["avg_recall"] + 0.35 * judge_norm + 0.30 * faith["avg_faithfulness"]


def demo_scorecard():
    print("=" * 60)
    print("PART 5: SCORECARD")
    print("=" * 60)
    print()

    runs = {
        "rag": {
            "retrieval": {"avg_recall": 0.50, "avg_precision": 0.33, "avg_mrr": 0.40},
            "judge": {"avg_correctness": 3.2, "avg_completeness": 2.8, "avg_relevance": 3.5},
            "faithfulness": {"avg_faithfulness": 0.62},
        },
        "rag_rerank": {
            "retrieval": {"avg_recall": 0.80, "avg_precision": 0.60, "avg_mrr": 0.85},
            "judge": {"avg_correctness": 4.1, "avg_completeness": 3.9, "avg_relevance": 4.4},
            "faithfulness": {"avg_faithfulness": 0.88},
        },
    }

    cards = []
    for name, run in runs.items():
        overall = overall_score(run["retrieval"], run["judge"], run["faithfulness"])
        cards.append((name, overall, run))
        print(
            f"  {name:12}  overall={overall:.3f}  "
            f"recall={run['retrieval']['avg_recall']:.2f}  "
            f"faith={run['faithfulness']['avg_faithfulness']:.2f}"
        )
    print()

    winner = max(cards, key=lambda row: row[1])
    print(f"  winner: {winner[0]}\n")

    floors = {"avg_recall": 0.6, "avg_faithfulness": 0.75, "overall": 0.55}
    for name, overall, run in cards:
        values = {
            "avg_recall": run["retrieval"]["avg_recall"],
            "avg_faithfulness": run["faithfulness"]["avg_faithfulness"],
            "overall": overall,
        }
        failures = [
            f"{metric} {values[metric]:.3f} < {floor}"
            for metric, floor in floors.items()
            if values[metric] < floor
        ]
        mark = "PASS" if not failures else "FAIL"
        print(f"  [{mark}] {name}")
        for fail in failures:
            print(f"         {fail}")
    print()


if __name__ == "__main__":
    demo_scorecard()
