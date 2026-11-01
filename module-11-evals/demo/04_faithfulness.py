"""Part 4: Which claims are actually in the source text?"""

CONTEXT = "Warp core operating at 94% efficiency. Minor fluctuation in plasma conduit 7-B."

ROWS = [
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


def demo_faithfulness():
    print("=" * 60)
    print("PART 4: FAITHFULNESS")
    print("=" * 60)
    print()
    print(f"  context: {CONTEXT}\n")

    for row in ROWS:
        supported = sum(1 for _, ok in row["claims"] if ok)
        total = len(row["claims"])
        print(f"  answer: {row['answer']}")
        for claim, ok in row["claims"]:
            print(f"    [{'ok' if ok else '!!'}] {claim}")
        print(f"    faithfulness = {supported}/{total} = {supported / total:.2f}\n")


if __name__ == "__main__":
    demo_faithfulness()
