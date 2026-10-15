"""
Module 11 Demo — Evals
Run:  python module-11-evals/demo/demo.py

Five parts, no API key:
  Part 1: Golden tests — mock LLM, tools + answer, pass/fail
  Part 2: Retrieval metrics — recall@k, precision@k, MRR
  Part 3: LLM-as-judge — canned scores, dataset summary
  Part 4: Faithfulness — claims vs context
  Part 5: Scorecard + gate — RAG vs RAG+rerank
"""

from __future__ import annotations

import json
from types import SimpleNamespace


def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def pause():
    try:
        input("  [Enter] continue  ")
    except (EOFError, KeyboardInterrupt):
        print()


# ---------------------------------------------------------------------------
# Part 1 — Golden tests
# ---------------------------------------------------------------------------

CREW = {
    "engineering": ["Mira Chen", "Bodhi Kwan"],
    "command": ["Elara Voss"],
}


def _scripted_client(script):
    queue = list(script)

    def create(**kwargs):
        item = queue.pop(0)
        if "tool_calls" in item:
            calls = [
                SimpleNamespace(
                    id=tc["id"],
                    function=SimpleNamespace(
                        name=tc["name"],
                        arguments=json.dumps(tc["arguments"]),
                    ),
                )
                for tc in item["tool_calls"]
            ]
            message = SimpleNamespace(content=None, tool_calls=calls)
        else:
            message = SimpleNamespace(content=item["content"], tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def run_golden_case(client, question: str) -> dict:
    tools = []
    answer = None
    messages = [{"role": "user", "content": question}]
    for _ in range(5):
        message = client.chat.completions.create(messages=messages).choices[0].message
        if message.tool_calls:
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                tools.append({"name": tc.function.name, "arguments": args})
                if tc.function.name == "get_crew_count":
                    dept = args["department"]
                    result = json.dumps({"count": len(CREW.get(dept, []))})
                else:
                    result = json.dumps({"error": "unknown"})
                messages.append({"role": "tool", "content": result})
        elif message.content:
            answer = message.content
            break
    return {"tools": tools, "answer": answer}


def demo_golden():
    section("Part 1: Golden tests — mock the LLM, assert tools + answer")

    print("  A golden case freezes one conversation:")
    print('    question: "How many people are in engineering?"')
    print("    expected tool: get_crew_count(department=engineering)")
    print('    expected answer: "Engineering has 2 crew members."')
    print()
    print("  The mock LLM returns a scripted tool_call, then a scripted final message.")
    print("  Handlers still run — we check behaviour, not the network.\n")
    pause()

    cases = [
        {
            "id": "crew-count-engineering",
            "question": "How many people are in engineering?",
            "script": [
                {
                    "tool_calls": [
                        {
                            "id": "c1",
                            "name": "get_crew_count",
                            "arguments": {"department": "engineering"},
                        }
                    ]
                },
                {"content": "Engineering has 2 crew members."},
            ],
            "expected_tools": [
                {"name": "get_crew_count", "arguments": {"department": "engineering"}}
            ],
            "expected_answer": "Engineering has 2 crew members.",
        },
        {
            "id": "wrong-department",
            "question": "How many people are in engineering?",
            "script": [
                {
                    "tool_calls": [
                        {
                            "id": "c1",
                            "name": "get_crew_count",
                            "arguments": {"department": "medical"},
                        }
                    ]
                },
                {"content": "Engineering has 2 crew members."},
            ],
            "expected_tools": [
                {"name": "get_crew_count", "arguments": {"department": "engineering"}}
            ],
            "expected_answer": "Engineering has 2 crew members.",
        },
    ]

    for case in cases:
        actual = run_golden_case(_scripted_client(case["script"]), case["question"])
        mismatches = []
        if actual["tools"] != case["expected_tools"]:
            mismatches.append("tools")
        if actual["answer"] != case["expected_answer"]:
            mismatches.append("answer")
        mark = "PASS" if not mismatches else "FAIL"
        print(f"  [{mark}] {case['id']}" + (f"  mismatches={mismatches}" if mismatches else ""))
        print(f"         tools={actual['tools']}")
        print(f"         answer={actual['answer']!r}")

    print()
    print("  Key concepts:")
    print("  • Mock the model; run the real loop and handlers")
    print("  • Exact match on tool names + arguments + final answer")
    print("  • Fast, free, deterministic — this belongs in pytest / CI")


# ---------------------------------------------------------------------------
# Part 2 — Retrieval metrics
# ---------------------------------------------------------------------------


def recall_at_k(ranked, relevant, k):
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & set(relevant)) / len(set(relevant))


def precision_at_k(ranked, relevant, k):
    if k <= 0:
        return 0.0
    return len(set(ranked[:k]) & set(relevant)) / k


def mrr(ranked, relevant):
    rel = set(relevant)
    for rank, doc_id in enumerate(ranked, start=1):
        if doc_id in rel:
            return 1.0 / rank
    return 0.0


def demo_retrieval():
    section("Part 2: Retrieval metrics — did we fetch the right logs?")

    print("  Labelled query: \"warp core efficiency\"")
    print("  Gold relevant:  LOG-002, LOG-011")
    print()
    naive = ["LOG-007", "LOG-016", "LOG-002"]
    rerank = ["LOG-002", "LOG-011", "LOG-007"]
    gold = ["LOG-002", "LOG-011"]
    print(f"  naive ranked:    {naive}")
    print(f"  reranked:        {rerank}")
    print()
    pause()

    k = 3
    print(f"  {'config':10}  recall@{k}  prec@{k}   MRR")
    for name, ranked in (("naive", naive), ("rerank", rerank)):
        print(
            f"  {name:10}  {recall_at_k(ranked, gold, k):8.2f}  "
            f"{precision_at_k(ranked, gold, k):7.2f}  {mrr(ranked, gold):5.2f}"
        )

    print()
    print("  Recall@k  — of the gold docs, how many did we retrieve?")
    print("  Precision@k — of the top k, how many were gold? (junk in the prompt)")
    print("  MRR         — 1/rank of the first relevant hit")
    print("  • Label 20 queries well. Re-run after every chunking / index change.")


# ---------------------------------------------------------------------------
# Part 3 — LLM-as-judge
# ---------------------------------------------------------------------------


def demo_judge():
    section("Part 3: LLM-as-judge — score answers, not word overlap")

    print("  BLEU/ROUGE punish paraphrase. A judge model reads:")
    print("    question + candidate + reference  →  JSON scores 1–5")
    print()
    cases = [
        {
            "question": "What causes warp core instability?",
            "answer": "Crystal degradation causes it.",
            "reference": (
                "Dilithium crystal degradation, plasma injection asymmetry, "
                "and magnetic containment fluctuations."
            ),
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
            "reference": "Chief Engineer Mira Chen leads engineering on Pathfinder.",
            "scores": {
                "correctness": 5,
                "completeness": 4,
                "relevance": 5,
                "explanation": "Name is right; omits the ship.",
            },
        },
    ]
    print("  Canned judge output (in CI you mock the client the same way):\n")
    for case in cases:
        s = case["scores"]
        print(f"  Q: {case['question']}")
        print(f"     A: {case['answer']}")
        print(
            f"     correctness={s['correctness']}  completeness={s['completeness']}  "
            f"relevance={s['relevance']}"
        )
        print(f"     {s['explanation']}\n")
    pause()

    n = len(cases)
    avg_c = sum(c["scores"]["correctness"] for c in cases) / n
    avg_p = sum(c["scores"]["completeness"] for c in cases) / n
    avg_r = sum(c["scores"]["relevance"] for c in cases) / n
    print(f"  summary  correctness={avg_c:.2f}  completeness={avg_p:.2f}  relevance={avg_r:.2f}")
    print()
    print("  Key concepts:")
    print("  • Temperature 0, JSON only, strip markdown fences")
    print("  • Treat scores as relative (config A vs B), not gospel")
    print("  • Spend tokens here when prompts change — not on every keystroke")


# ---------------------------------------------------------------------------
# Part 4 — Faithfulness
# ---------------------------------------------------------------------------


def demo_faithfulness():
    section("Part 4: Faithfulness — is every claim in the retrieved context?")

    print("  Judge scores vs a reference. Faithfulness scores vs the *sources*.")
    print("  Split the answer into claims; check each one against the log.\n")

    context = (
        "Warp core operating at 94% efficiency. Minor fluctuation in plasma conduit 7-B."
    )
    rows = [
        {
            "answer": (
                "The warp core is at 94% efficiency. "
                "Plasma conduit 7-B has a minor fluctuation."
            ),
            "claims": [
                ("The warp core is at 94% efficiency.", True),
                ("Plasma conduit 7-B has a minor fluctuation.", True),
            ],
        },
        {
            "answer": "The warp core is at 94% efficiency. Core temperature is 9000K.",
            "claims": [
                ("The warp core is at 94% efficiency.", True),
                ("Core temperature is 9000K.", False),
            ],
        },
    ]
    print(f"  context: {context}\n")
    pause()

    for row in rows:
        n_ok = sum(1 for _, ok in row["claims"] if ok)
        n = len(row["claims"])
        ratio = n_ok / n
        print(f"  answer: {row['answer']}")
        for claim, ok in row["claims"]:
            print(f"    [{'ok' if ok else '!!'}] {claim}")
        print(f"    faithfulness = {n_ok}/{n} = {ratio:.2f}\n")

    print("  Key concepts:")
    print("  • Zero claims → 1.0 (nothing to hallucinate)")
    print("  • Cousin of citation verification — here you want a ratio for the scorecard")


# ---------------------------------------------------------------------------
# Part 5 — Scorecard + gate
# ---------------------------------------------------------------------------


def overall_score(retrieval, judge, faith):
    judge_norm = (
        judge["avg_correctness"] + judge["avg_completeness"] + judge["avg_relevance"]
    ) / 15.0
    return 0.35 * retrieval["avg_recall"] + 0.35 * judge_norm + 0.30 * faith["avg_faithfulness"]


def demo_scorecard():
    section("Part 5: Scorecard + gate — pick a winner, fail a bad release")

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
    print("  Same questions, two pipelines. overall =")
    print("    0.35*recall + 0.35*judge_norm + 0.30*faithfulness")
    print()
    cards = []
    for name, run in runs.items():
        overall = overall_score(run["retrieval"], run["judge"], run["faithfulness"])
        cards.append((name, overall, run))
        print(
            f"  {name:12}  overall={overall:.3f}  "
            f"recall={run['retrieval']['avg_recall']:.2f}  "
            f"faith={run['faithfulness']['avg_faithfulness']:.2f}"
        )
    pause()

    winner = max(cards, key=lambda row: row[1])
    print(f"  winner: {winner[0]}")
    print()
    floors = {"avg_recall": 0.6, "avg_faithfulness": 0.75, "overall": 0.55}
    print(f"  release floors: {floors}\n")
    for name, overall, run in cards:
        failures = []
        values = {
            "avg_recall": run["retrieval"]["avg_recall"],
            "avg_faithfulness": run["faithfulness"]["avg_faithfulness"],
            "overall": overall,
        }
        for metric, floor in floors.items():
            if values[metric] < floor:
                failures.append(f"{metric} {values[metric]:.3f} < {floor}")
        mark = "PASS" if not failures else "FAIL"
        print(f"  [{mark}] {name}")
        for fail in failures:
            print(f"         {fail}")

    print()
    print("  Key concepts:")
    print("  • Compare on a delta (which config wins)")
    print("  • Gate on a floor (is it good enough to ship?)")
    print("  • Module 12 capstones can reuse this as a release check")


DEMOS = {
    "1": ("Golden tests", demo_golden),
    "2": ("Retrieval metrics", demo_retrieval),
    "3": ("LLM-as-judge", demo_judge),
    "4": ("Faithfulness", demo_faithfulness),
    "5": ("Scorecard + gate", demo_scorecard),
}


if __name__ == "__main__":
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
            for _, fn in DEMOS.values():
                fn()
            continue
        if choice in DEMOS:
            DEMOS[choice][1]()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. Golden tests      — mock LLM, assert tools + answer (CI)")
    print("  2. Retrieval metrics — recall@k, precision@k, MRR")
    print("  3. LLM-as-judge      — correctness, completeness, relevance")
    print("  4. Faithfulness      — claims grounded in retrieved context")
    print("  5. Scorecard + gate  — pick a winner, fail a bad release")
    print()
    print("=" * 60)
