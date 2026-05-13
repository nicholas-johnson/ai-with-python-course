# Exercise 01 — Retrieval Router

## Mission

Not every question needs a vector search. Build a retrieval router that classifies queries and dispatches them to the right backend.

## Objectives

1. Define a `RetrievalBackend` enum with at least `VECTOR`, `GRAPH`, and `KEYWORD`.
2. Implement `classify_query(query: str) -> RoutingDecision` that picks the best backend.
3. Implement `route_and_retrieve(query, backends) -> list[dict]` that calls the chosen backend's retrieval function.

## Constraints

- `classify_query` must return a `RoutingDecision` with `backend`, `confidence` (0-1), and `reasoning`.
- Relationship-style queries ("who", "connected to", "relationship between") should route to `GRAPH`.
- Exact-match queries ("error code", "log entry", "serial number") should route to `KEYWORD`.
- Everything else defaults to `VECTOR`.

## Run

```bash
pytest module-09-adaptive-retrieval/exercises/01-retrieval-router/test_start.py -v
```
