# Exercise 02 — Vector Search

**Mission briefing:** **Embed** mission archive text and run **similarity search** to retrieve the top-k chunks for a query. Use a small local embedding model or API stub as directed in class.

## Objectives

1. Build an in-memory store of vectors + metadata from chunked documents.
2. Implement `search(query: str, k: int) -> list[dict]`.
3. Return scores and chunk text for downstream RAG.

## Run the tests

```bash
pytest module-06-rag-fundamentals/exercises/02-vector-search/test_start.py -v
```
