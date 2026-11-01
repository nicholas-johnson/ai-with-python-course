"""Part 1: Fuse two rankings. No documents, no model.
Run alone:  python module-13-edge-topics/demo/01_rrf.py
"""


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranked in rankings:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


def demo_rrf():
    print("=" * 60)
    print("PART 1: RECIPROCAL RANK FUSION")
    print("=" * 60)
    print()

    keyword = ["doc5", "doc1", "doc2"]
    vector = ["doc1", "doc5", "doc8"]
    fused = reciprocal_rank_fusion([keyword, vector])

    print(f"  keyword: {keyword}")
    print(f"  vector:  {vector}")
    print(f"  fused:   {fused}")
    print()


if __name__ == "__main__":
    demo_rrf()
