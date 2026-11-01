"""Part 3: Canned judge scores, then the averages."""

CASES = [
    {
        "question": "What causes warp core instability?",
        "answer": "Crystal degradation causes it.",
        "scores": {
            "correctness": 5,
            "completeness": 2,
            "relevance": 5,
            "explanation": "Correct but only one of three causes.",
        },
    },
    {
        "question": "Who leads engineering?",
        "answer": "Chief Engineer Mira Chen.",
        "scores": {
            "correctness": 5,
            "completeness": 4,
            "relevance": 5,
            "explanation": "Name is right; omits the ship.",
        },
    },
]


def demo_judge():
    print("=" * 60)
    print("PART 3: LLM-AS-JUDGE")
    print("=" * 60)
    print()

    for case in CASES:
        scores = case["scores"]
        print(f"  Q: {case['question']}")
        print(f"     A: {case['answer']}")
        print(
            f"     correctness={scores['correctness']}  "
            f"completeness={scores['completeness']}  relevance={scores['relevance']}"
        )
        print(f"     {scores['explanation']}\n")

    n = len(CASES)
    avg_c = sum(case["scores"]["correctness"] for case in CASES) / n
    avg_p = sum(case["scores"]["completeness"] for case in CASES) / n
    avg_r = sum(case["scores"]["relevance"] for case in CASES) / n
    print(f"  summary  correctness={avg_c:.2f}  completeness={avg_p:.2f}  relevance={avg_r:.2f}")
    print()


if __name__ == "__main__":
    demo_judge()
