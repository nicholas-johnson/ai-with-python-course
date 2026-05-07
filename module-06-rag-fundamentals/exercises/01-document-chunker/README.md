# Exercise 01 — Document Chunker

**Mission briefing:** Split Pathfinder **ship logs** into overlapping text windows so they can be embedded and retrieved. Implement chunk size, overlap, and clear chunk metadata (e.g. source id, offset).

## Objectives

1. Load log text (from fixtures or `data/ship_logs.json`).
2. Produce a list of chunks with configurable `chunk_size` and `overlap`.
3. Each chunk should carry metadata useful for later citation (source, index).

## Run the tests

```bash
pytest module-06-rag-fundamentals/exercises/01-document-chunker/test_start.py -v
```
