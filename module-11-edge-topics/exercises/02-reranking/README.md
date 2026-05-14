# Exercise 02 — Re-ranking

## Recap

Initial retrieval casts a wide net for recall, but ranking precision is low. A **re-ranker** applies a more expensive model (cross-encoder or LLM) to the top-N results, scoring each (query, passage) pair for relevance. This two-stage pipeline gives you speed from retrieval and precision from re-ranking.

## Your Task

1. Implement `score_relevance(query, passage)` — score a single passage against a query (0-10).
2. Implement `rerank(query, passages, top_k)` — re-rank all passages and return the top-k.
3. Implement `two_stage_retrieve(query, retrieve_fn, rerank_fn, retrieve_k, final_k)` — full pipeline.

## Steps

1. Open `start.py` and review the function signatures.
2. Implement `score_relevance` using an LLM call that returns a numeric score.
3. Implement `rerank` by scoring each passage and sorting by score.
4. Wire it together in `two_stage_retrieve`.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/02-reranking/test_start.py -v
```

## Stretch Goals

- Batch multiple passages into a single LLM call for efficiency.
- Compare LLM re-ranking quality against a simple keyword-overlap scorer.
- Add caching so repeated (query, passage) pairs are not re-scored.
