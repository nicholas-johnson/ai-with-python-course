# Exercise 01 — Structured Outputs

**Goal:** Get GPT to return reliable, parseable JSON every time. You will build a console app that takes a free-text description and returns a validated Pydantic model.

## What you build

1. A `MissionReport` Pydantic model with fields: `mission_id` (str), `status` (literal), `risk_level` (literal), `summary` (str).
2. A `SYSTEM_PROMPT` that constrains the model to return JSON matching the schema.
3. An `analyse(client, text)` function that calls `client.chat.completions.create` with `response_format={"type": "json_object"}` and validates the response with Pydantic.
4. A `main()` loop: type a mission description, get a structured report back.

## Run it

```bash
python start.py
```

## Run the tests

```bash
pytest module-04-genai-strategies/exercises/01-structured-outputs/test_start.py -v
```
