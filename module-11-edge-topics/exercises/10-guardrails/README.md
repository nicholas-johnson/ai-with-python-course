# Exercise 10 — Advanced Guardrails

## Recap

Production LLM systems need defence in depth: **content filtering** catches toxic or off-topic input, **PII detection** redacts personal information, and **schema validation** ensures structured outputs conform to expectations. A guardrail pipeline chains these checks sequentially.

## Your Task

1. Implement `check_content(text, blocked_patterns)` — check text against blocked regex patterns.
2. Implement `redact_pii(text)` — find and redact emails, phone numbers, and SSNs.
3. Implement `validate_output(data, schema_class)` — validate a dict against a Pydantic model.
4. Implement `guardrail_pipeline(text, blocked_patterns, schema_class)` — chain all three checks.

## Steps

1. Open `start.py` and review the function signatures and the `SafeResponse` Pydantic model.
2. Implement `check_content`: regex search for blocked patterns.
3. Implement `redact_pii`: use regex to find and replace PII patterns.
4. Implement `validate_output`: use Pydantic to validate the data.
5. Chain them in `guardrail_pipeline`.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/10-guardrails/test_start.py -v
```

## Stretch Goals

- Add an LLM-based content classifier for nuanced filtering.
- Add name detection using simple heuristics (capitalised words after "Mr./Ms.").
- Add rate limiting as an additional guardrail layer.
