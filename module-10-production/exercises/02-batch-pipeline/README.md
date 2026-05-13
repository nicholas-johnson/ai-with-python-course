# Exercise 02 — Batch Pipeline

**Mission briefing:** Send **multiple prompts** through a pipeline that applies **retry with backoff** on transient failures and falls back to a **cheaper stub model** when the primary exhausts retries.

## Objectives

1. Implement `async def complete_batch(prompts: list[str]) -> list[str]` (or sync if preferred).
2. Retry up to N times on a simulated `TransientError`.
3. On hard failure, use `fallback_complete(prompt: str) -> str`.

## Run the tests

```bash
pytest module-10-production/exercises/02-batch-pipeline/test_start.py -v
```
