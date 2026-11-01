# Exercise 02 — Retrieval Metrics

## Recap

A RAG index that feels good in a demo can still miss the one log that answers the question. To know whether it does, you need a **labelled set**: for each query, the document IDs that should come back. Three numbers cover most of what you need.

- **Recall@k** — of all the relevant documents, what fraction appear in the top *k*? This tells you whether you missed the evidence.
- **Precision@k** — of the top *k* results, what fraction are relevant? This tells you how much junk you are pushing into the prompt.
- **MRR** (mean reciprocal rank) — `1 / rank` of the *first* relevant document. This rewards putting a good hit near the top.

Worked through on one query:

```
ranked     = [LOG-007, LOG-002, LOG-016]   # what the index returned
relevant   = [LOG-002, LOG-011]            # the gold labels
k          = 3

recall@3    = 1/2 = 0.50   # found LOG-002, missed LOG-011
precision@3 = 1/3 = 0.33   # one of three results was relevant
MRR         = 1/2 = 0.50   # the first relevant hit was at rank 2
```

These functions are pure. They never call an LLM or a vector store, so you can test them without an API key and they run instantly in CI.

This is the first of four measurements that feed the scorecard in [exercise 05](../05-eval-compare/). The same five questions run through the same two pipeline configs in exercises 03 and 04, so the numbers you produce here are the ones you will compare against later.

### The two configs

`data/ranked_runs.json` holds what each pipeline returned for the five labelled questions:

| Config | What it is |
|---|---|
| `rag` | Plain dense retrieval, top 5 |
| `rag_rerank` | The same retrieval with a reranking pass over the results |

Reranking should push gold documents up the list. Watch whether it does that on every query.

## What you build

| Function | What it does |
|---|---|
| `recall_at_k(ranked_ids, relevant_ids, k)` | Relevant documents found in the top k, over the total relevant |
| `precision_at_k(ranked_ids, relevant_ids, k)` | Relevant documents found in the top k, over k |
| `mrr(ranked_ids, relevant_ids)` | `1 / rank` of the first relevant document, else `0.0` |
| `evaluate_queries(queries, k)` | Attach recall, precision and MRR to each query |
| `summarize(evaluations)` | Average the three metrics and count the queries |

Three edge cases to get right: an empty `relevant_ids` gives a recall of `0.0`, a `k` of `0` gives a precision of `0.0`, and precision **always divides by k** even when the index returned fewer than k documents, so a short result list is penalised rather than flattered.

Each query in `evaluate_queries` looks like this:

```python
{
    "query": "What is the current warp core efficiency?",
    "ranked_ids": ["LOG-007", "LOG-002", "LOG-016", "LOG-011", "LOG-005"],
    "relevant_ids": ["LOG-002", "LOG-011"],
}
```

`summarize` returns the averages:

```python
{"avg_recall": 0.5, "avg_precision": 0.27, "avg_mrr": 0.52, "num_queries": 5}
```

## Step-by-step

### 1. Implement `recall_at_k`

Take the first k entries of `ranked_ids` and intersect them with `relevant_ids`, then divide by the number of relevant documents. Converting both to sets makes the intersection straightforward. Return `0.0` when there are no relevant documents, rather than dividing by zero.

### 2. Implement `precision_at_k`

Use the same intersection, but divide by `k` instead of by the number of relevant documents. Guard against a `k` of zero.

### 3. Implement `mrr`

Walk `ranked_ids` keeping a 1-based rank. As soon as you hit a document that is in `relevant_ids`, return `1.0 / rank`. If you reach the end without a hit, return `0.0`.

### 4. Implement `evaluate_queries` and `summarize`

`evaluate_queries` loops over the queries and attaches the three metrics to each one, leaving the original keys in place. `summarize` averages each metric across that list and reports how many queries it saw. Both need to cope with an empty list.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/02-retrieval-metrics
python start.py

# Option B - uv (no activation needed):
cd module-11-evals/exercises/02-retrieval-metrics
uv run python start.py
```

This scores both configs on `data/labeled_queries.json` and then prints recall per query. Reranking wins overall, but look at the per-query breakdown before you celebrate: it drops the one query where the relevant log is the only document on its topic. That is the kind of thing an average buries, and it is why [exercise 05](../05-eval-compare/) gates on a floor instead of trusting one number.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/02-retrieval-metrics
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-11-evals/exercises/02-retrieval-metrics
uv run --extra dev pytest test_start.py -v
```

The tests check:

- `recall_at_k` handles a full hit, a partial hit, no hits, and an empty label set
- `recall_at_k` respects the k cut-off when a relevant document sits just below it
- `precision_at_k` divides by k rather than by the number of results returned
- `mrr` finds the first relevant document and returns `0.0` when there is none
- `evaluate_queries` attaches all three metrics and keeps the original keys
- `summarize` averages correctly and returns zeros for an empty list

## Stretch goals

- Add nDCG@k so you can score graded relevance rather than a binary relevant-or-not label.
- Run the same labelled queries against the Module 5 Chroma index at two chunk sizes and print both summaries.
- Plot recall against k for k of 1, 3, 5 and 10 for each config, and find the point where more context stops helping.
