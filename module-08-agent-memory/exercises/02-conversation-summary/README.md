# Exercise 02 — Conversation Summary

**Mission briefing:** Given a long list of chat turns, produce a **single summary string** that fits under a **max_tokens** budget (approximate counting is fine). Drop oldest turns first if needed, then summarise what remains.

## Objectives

1. `trim_turns(turns, max_tokens) -> list[dict]` — FIFO trim by rough token count.
2. `summarise_turns(turns, max_tokens) -> str` — compress to one paragraph under budget.

## Run the tests

```bash
pytest module-08-agent-memory/exercises/02-conversation-summary/test_start.py -v
```
