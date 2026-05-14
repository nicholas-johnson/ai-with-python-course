# Exercise 01 — Hybrid Search

## Recap

Hybrid search combines vector (semantic) search with keyword (BM25) search and merges the results using **Reciprocal Rank Fusion (RRF)**. Each retrieval method has strengths the other lacks — combining them gives consistently better results.

## Your Task

1. Implement `bm25_search(query, documents)` — a simple keyword-based search using term frequency.
2. Implement `reciprocal_rank_fusion(ranked_lists, k=60)` — merge multiple ranked lists using RRF scoring.
3. Implement `hybrid_search(query, documents, embeddings, top_k=5)` — run both searches and fuse the results.

## Steps

1. Open `start.py` and read through the function signatures and TODOs.
2. Implement `bm25_search`: tokenise query and documents, score by term overlap, return ranked doc IDs.
3. Implement `reciprocal_rank_fusion`: for each doc across all lists, accumulate `1 / (k + rank)`.
4. Implement `hybrid_search`: call both search functions, fuse with RRF, return top-k.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/01-hybrid-search/test_start.py -v
```

## Stretch Goals

- Add TF-IDF weighting instead of raw term frequency.
- Experiment with different `k` values and observe how it affects fusion.
- Add a weight parameter to bias toward vector or keyword results.
