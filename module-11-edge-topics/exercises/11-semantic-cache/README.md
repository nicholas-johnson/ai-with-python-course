# Exercise 11 — Semantic Caching

## Recap

Traditional caching requires exact query matches. **Semantic caching** uses embedding similarity to recognise paraphrased questions and return cached responses. "What is France's capital?" and "Capital of France?" are semantically identical and should hit the same cache entry.

## Your Task

1. Implement `cosine_similarity(a, b)` — compute cosine similarity between two vectors.
2. Implement `SemanticCache` class with `get(query)` and `set(query, response)` methods.
3. The cache should find entries above a similarity threshold and support TTL expiration.

## Steps

1. Open `start.py` and review the `SemanticCache` class skeleton.
2. Implement `cosine_similarity` using dot product and norms.
3. Implement `get`: embed the query, compare against all cache entries, return if above threshold.
4. Implement `set`: embed the query, store with response and timestamp.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/11-semantic-cache/test_start.py -v
```

## Stretch Goals

- Add TTL (time-to-live) so old entries expire automatically.
- Use a vector database (chromadb) as the cache backend for scalability.
- Add cache statistics (hit rate, miss rate, average similarity).
