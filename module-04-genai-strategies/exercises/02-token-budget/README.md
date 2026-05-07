# Exercise 02 — Token Budget

**Mission briefing:** Implement **token counting** (approximate or library-based) and **refuse or trim** requests that exceed a configured budget before they hit the model.

## Objectives

1. Implement `count_tokens(text: str) -> int` (simple whitespace split is OK for skeleton; upgrade to tiktoken in class).
2. Implement `enforce_budget(messages: list[str], max_tokens: int) -> list[str]` that drops or truncates from the oldest user turns.

## Run the tests

```bash
pytest module-04-genai-strategies/exercises/02-token-budget/test_start.py -v
```
