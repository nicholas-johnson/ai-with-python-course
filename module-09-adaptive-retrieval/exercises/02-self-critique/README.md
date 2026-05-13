# Exercise 02 — Self-Critique Retrieval

## Mission

First-pass retrieval isn't always good enough. Build a corrective retrieval loop that evaluates result quality and re-queries with refined terms when needed.

## Objectives

1. Implement `critique_results(query, docs, threshold) -> CritiqueResult` that evaluates average relevance and decides pass/fail.
2. Implement `refine_query(query, critique) -> str` that produces a better query based on the critique.
3. Implement `retrieval_loop(query, retrieve_fn, max_attempts, threshold) -> tuple[list, int]` that loops: retrieve → critique → refine until quality is sufficient or attempts are exhausted.

## Constraints

- `CritiqueResult` has `is_sufficient: bool`, `avg_relevance: float`, and `suggestion: str`.
- The loop must stop early when results pass the threshold.
- Must not exceed `max_attempts` iterations.

## Run

```bash
pytest module-09-adaptive-retrieval/exercises/02-self-critique/test_start.py -v
```
