# Exercise 13 — Contextual Chunking

## Recap

How you chunk documents has a massive impact on retrieval quality. **Parent-child chunking** uses small chunks for precise matching but retrieves the larger parent chunk for generation context. **Overlapping windows** ensure boundary information is not lost. **Semantic chunking** splits at natural topic boundaries.

## Your Task

1. Implement `fixed_chunk(text, chunk_size)` — basic fixed-size word chunking.
2. Implement `overlap_chunk(text, chunk_size, overlap)` — chunking with overlapping windows.
3. Implement `parent_child_chunk(text, parent_size, child_size)` — two-level parent-child chunking.
4. Implement `retrieve_with_context(query_embedding, child_chunks, parent_chunks, top_k)` — search children, return parents.

## Steps

1. Open `start.py` and review the function signatures.
2. Implement `fixed_chunk`: split text by words, group into chunks of `chunk_size`.
3. Implement `overlap_chunk`: like fixed_chunk but with overlapping windows.
4. Implement `parent_child_chunk`: create parent chunks, then split each into child chunks.
5. Implement `retrieve_with_context`: find best child matches, return their parent chunks.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/13-contextual-chunking/test_start.py -v
```

## Stretch Goals

- Implement semantic chunking using sentence-level similarity drop-off.
- Compare retrieval quality across different chunking strategies.
- Add metadata tracking (chunk position, parent-child relationships).
