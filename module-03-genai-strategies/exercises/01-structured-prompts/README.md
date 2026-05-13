# Exercise 01 — Structured Prompts

**Mission briefing:** Craft system + user prompts so the model returns **valid JSON** every time (within tolerance). Use a stub "model" in tests if no API key is available.

## Objectives

1. Define a Pydantic or TypedDict schema for a small "mission status" object.
2. Build a prompt that asks for **only** JSON matching that schema.
3. Parse and validate the response; surface clear errors on failure.

## Run the tests

```bash
pytest module-03-genai-strategies/exercises/01-structured-prompts/test_start.py -v
```
