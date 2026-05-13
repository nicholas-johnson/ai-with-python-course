# Exercise 03 — Guarded Agent

**Mission briefing:** An unguarded AI can call any tool at any rate — that is a hull breach waiting to happen. Wrap your tool-calling agent with safety rails: an allowlist that restricts which tools can be called, a rate limiter that prevents runaway loops, and an audit log that records everything.

This exercise builds on Exercise 02. The `ToolRegistry`, tool registrations, and agent loop are already provided — you only need to implement the safety classes and the `GuardedAgent`.

## Objectives

1. Implement `AllowList(permitted)` — checks whether a tool name is permitted.
2. Implement `RateLimiter(max_calls, window_seconds)` — sliding-window rate limit.
3. Implement `GuardedAgent` — wraps the agent loop with allowlist + rate limit checks and an audit log.
4. The agent should tell the model when a tool is blocked (so it can explain or try something else).

## Try it

```bash
python start.py
```

Try asking about crew, ship status, and crew searches. Notice that `search_crew` is deliberately excluded from the allowlist — watch how the model handles being told a tool is blocked.

## Run the tests

```bash
pytest module-02-agent-core/exercises/03-guarded-agent/test_start.py -v
```
