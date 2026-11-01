"""Part 2: recall@k, precision@k, and MRR on two rankings."""


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
    print("=" * 60)
    print("PART 2: RETRIEVAL METRICS")
    print("=" * 60)
    print()

    naive = ["LOG-007", "LOG-016", "LOG-002"]
    rerank = ["LOG-002", "LOG-011", "LOG-007"]
    gold = ["LOG-002", "LOG-011"]
    print('  Query: "warp core efficiency"')
    print(f"  Gold:    {gold}")
    print(f"  naive:   {naive}")
    print(f"  rerank:  {rerank}\n")

    k = 3
    print(f"  {'config':10}  recall@{k}  prec@{k}   MRR")
    for name, ranked in (("naive", naive), ("rerank", rerank)):
        print(
            f"  {name:10}  {recall_at_k(ranked, gold, k):8.2f}  "
            f"{precision_at_k(ranked, gold, k):7.2f}  {mrr(ranked, gold):5.2f}"
        )
    print()


if __name__ == "__main__":
    demo_retrieval()
