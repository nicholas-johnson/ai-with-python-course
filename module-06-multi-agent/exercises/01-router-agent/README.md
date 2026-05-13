# Exercise 01 — Router agent

**Mission briefing:** Build a router that classifies incoming crew or command messages and forwards them to the right specialist agent stub (navigation, engineering, science).

## Objectives

1. Implement intent or keyword routing with a clear fallback path.
2. Keep a single user-facing entrypoint while delegating to specialists.
3. Return which specialist handled the request for observability.

## Run the tests

```bash
pytest module-06-multi-agent/exercises/01-router-agent/test_start.py -v
```
