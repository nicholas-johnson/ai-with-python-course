"""
Module 11 Demo — Evals
Run:  python module-11-evals/demo/demo.py

  Part 1: Golden tests — two agent builds against one frozen reference
  Part 2: Retrieval metrics
  Part 3: LLM-as-judge
  Part 4: Faithfulness
  Part 5: Scorecard + gate

No API key. Scripted data only.
"""

from importlib import import_module

demo_golden = import_module("01_golden").demo_golden
demo_retrieval = import_module("02_retrieval").demo_retrieval
demo_judge = import_module("03_judge").demo_judge
demo_faithfulness = import_module("04_faithfulness").demo_faithfulness
demo_scorecard = import_module("05_scorecard").demo_scorecard

DEMOS = {
    "1": ("Golden tests", demo_golden),
    "2": ("Retrieval metrics", demo_retrieval),
    "3": ("LLM-as-judge", demo_judge),
    "4": ("Faithfulness", demo_faithfulness),
    "5": ("Scorecard + gate", demo_scorecard),
}


def main():
    print("\n" + "=" * 60)
    print("  MODULE 11 DEMO — EVALS")
    print("=" * 60)
    print("  No API key. Scripted data only.")

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  a. All")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        if choice == "a":
            print()
            for _, fn in DEMOS.values():
                fn()
            continue
        if choice in DEMOS:
            print()
            DEMOS[choice][1]()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. Golden tests      — frozen reference catches the drifted build")
    print("  2. Retrieval metrics — recall@k, precision@k, MRR")
    print("  3. LLM-as-judge      — correctness, completeness, relevance")
    print("  4. Faithfulness      — claims grounded in the retrieved text")
    print("  5. Scorecard + gate  — pick a winner, fail a bad release")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
