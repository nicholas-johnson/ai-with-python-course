# Exercise 03 — Safety Rails + Evaluation

**Mission briefing:** An unguarded AI can call any tool at any rate — that's a hull breach waiting to happen. Build a safety layer with rate limiting, then write golden-file tests to prove your agent behaves correctly under controlled conditions.

## Objectives

1. Implement `RateLimiter(max_calls, window_seconds)` — tracks call timestamps and returns whether a new call is allowed.
2. Implement `SafeToolRunner(registry, rate_limiter, allowed_tools)` — wraps a tool registry call with allowlist + rate limit checks, returning structured errors for blocked calls.
3. Implement `run_golden_test(case, llm, tools)` — execute an agent loop with a mock LLM and compare tool calls + final answer against expected values. Return a pass/fail result.

## Run the tests

```bash
pytest module-02-agent-core/exercises/03-safety-eval/test_start.py -v
```
