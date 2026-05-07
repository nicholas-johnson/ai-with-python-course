# Exercise 03 — Guardrail Chain

**Mission briefing:** Run model output through a **chain**: JSON/schema validation → **content filter** (simple blocklist or regex) → **confidence** threshold. Return structured pass/fail + reasons.

## Objectives

1. `validate_schema(payload: dict) -> tuple[bool, str]`
2. `content_filter(text: str) -> tuple[bool, str]`
3. `run_guardrails(raw: dict, min_confidence: float) -> dict` combining all checks

## Run the tests

```bash
pytest module-04-genai-strategies/exercises/03-guardrail-chain/test_start.py -v
```
