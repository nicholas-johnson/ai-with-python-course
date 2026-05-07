# Exercise 01 — Memory Store

**Mission briefing:** Implement **short-term** (session) and **long-term** (profile) memory for a Pathfinder agent. Long-term entries should **decay** (lose relevance score over time) unless refreshed.

## Objectives

1. `SessionMemory` — append messages, cap length or token estimate.
2. `LongTermMemory` — `remember(key, value)`, `recall(query)`, `tick_decay()` lowers scores.
3. Support a **"forget"** flag on remember to exclude from recall immediately.

## Run the tests

```bash
pytest module-08-agent-memory/exercises/01-memory-store/test_start.py -v
```
