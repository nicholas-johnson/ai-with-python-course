# Exercise 03 — RAG Pipeline

**Mission briefing:** Wire **retrieve → prompt → (mock) generate** so answers cite **which chunk** they came from. No production LLM required if the exercise uses a stub generator.

## Objectives

1. Given a user question, retrieve top-k chunks from your store.
2. Build a prompt that includes quoted passages and asks for an answer + citation ids.
3. Parse or structure output so each claim links to `chunk_id` (or equivalent).

## Run the tests

```bash
pytest module-05-rag-fundamentals/exercises/03-rag-pipeline/test_start.py -v
```
