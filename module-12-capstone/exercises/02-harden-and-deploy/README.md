# Exercise 02 — Harden and deploy

**Mission briefing:** The Pathfinder Operations AI works on your laptop — now make it production-ready. Add structured tracing so you can debug any request, wrap LLM calls with retries and a circuit breaker, enforce token budgets, and package everything in a Docker container with a health check.

## Objectives

1. Add a `TraceContext` that assigns a trace ID to each request and records spans for LLM calls and tool invocations.
2. Implement `retry_with_backoff` that retries transient failures with exponential backoff and jitter.
3. Build a `CircuitBreaker` that opens after repeated failures and recovers after a cooldown.
4. Create a `CostTracker` that records token usage and enforces session and daily budgets.
5. Implement `create_app` (FastAPI with `/health`), `load_config` (env-based settings), and `validate_dockerfile`.

## Run the tests

```bash
pytest module-12-capstone/exercises/02-harden-and-deploy/test_start.py -v
```
