# Exercise 01 — Fact Extractor

## Mission

The Pathfinder's logs are unstructured prose. Your job: build an extraction pipeline that turns raw text into structured `Fact` objects with provenance tracking.

## Objectives

1. Define a **Pydantic model** (`Fact`) with fields: `subject`, `predicate`, `object`, `source_text`, and `confidence`.
2. Write `extract_facts(text: str) -> list[Fact]` that uses an LLM prompt to pull structured facts from a passage.
3. Write `validate_facts(facts: list[Fact]) -> list[Fact]` that filters out facts with confidence below a threshold and deduplicates by (subject, predicate, object).

## Constraints

- All LLM calls go through the provided `mock_llm` fixture in tests — no real API key needed.
- `extract_facts` must return valid `Fact` instances (Pydantic validation must pass).
- `validate_facts` must drop facts with `confidence < 0.7` and keep only the highest-confidence duplicate.

## Run

```bash
pytest module-08-structured-facts/exercises/01-fact-extractor/test_start.py -v
```
