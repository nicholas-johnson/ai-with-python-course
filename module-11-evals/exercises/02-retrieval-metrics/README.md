# Exercise 02 — Retrieval Metrics

## Recap

A RAG index that "feels" good in a demo can still miss the one log that answers the question. **Retrieval metrics** need a labelled set: for each query, the document IDs that *should* come back.

Three numbers cover most teaching (and a surprising amount of production):

- **Recall@k** — of all relevant docs, what fraction appear in the top *k*? Did we miss evidence?
- **Precision@k** — of the top *k*, what fraction are relevant? How much junk did we stuff into the prompt?
- **MRR** — `1 / rank` of the *first* relevant doc. Did a good hit land near the top?

```
ranked     = [LOG-007, LOG-002, LOG-011]   # what the index returned
relevant   = [LOG-002, LOG-011]            # gold labels
k          = 3

recall@3    = 2/2 = 1.0
precision@3 = 2/3 ≈ 0.67
MRR         = 1/2 = 0.5     # first relevant is rank 2
```

These functions are pure: they never call an LLM or a vector store. You can pytest them without an API key. Stretch: wire them to the Module 5 Chroma index and compare chunk sizes.

## What you build

| Function | What it does |
|---|---|
| `recall_at_k(ranked_ids, relevant_ids, k)` | `\|top_k ∩ relevant\| / \|relevant\|` |
| `precision_at_k(ranked_ids, relevant_ids, k)` | `\|top_k ∩ relevant\| / k` |
| `mrr(ranked_ids, relevant_ids)` | `1 / rank` of first relevant, else `0.0` |
| `evaluate_queries(queries, k)` | Attach recall/precision/mrr to each query |
| `summarize(evaluations)` | Averages + `num_queries` |

Empty `relevant_ids` → recall `0.0`. `k == 0` → precision `0.0`. Precision **always divides by k**, even if fewer than k docs were returned.

Each query in `evaluate_queries`:

```python
{
    "query": "warp core efficiency",
    "ranked_ids": ["LOG-007", "LOG-002", "LOG-011"],
    "relevant_ids": ["LOG-002", "LOG-011"],
}
```

`summarize` returns:

```python
{"avg_recall": 0.8, "avg_precision": 0.5, "avg_mrr": 0.7, "num_queries": 5}
```

## Step-by-step

### 1. `recall_at_k`

Take `ranked_ids[:k]`. Intersection size over `len(relevant_ids)`. Sets are the easy way.

### 2. `precision_at_k`

Same intersection, divide by `k` (not by `len(top)`).

### 3. `mrr`

Walk `ranked_ids` with a 1-based rank. Return `1.0 / rank` on the first hit in `relevant_ids`. No hit → `0.0`.

### 4. `evaluate_queries` / `summarize`

Loop, attach three floats, then average. Empty list → zeros.

## Try it

```bash
cd module-11-evals/exercises/02-retrieval-metrics
python start.py
```

Compares a **naive** ranked run to a **reranked** run on `data/labeled_queries.json`. The reranked lists should win.

## Running Tests

```bash
pytest module-11-evals/exercises/02-retrieval-metrics/test_start.py -v
```

## Stretch Goals

- Add nDCG@k (graded relevance, not just binary).
- Run the same labelled queries against the Module 5 Chroma index at two chunk sizes and print both summaries.
- Plot recall vs k (k = 1, 3, 5, 10) for each config.
