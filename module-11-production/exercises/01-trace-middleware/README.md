# Exercise 01 — Trace middleware

**Mission briefing:** Wrap tool execution so every call receives a trace id, records start/end timestamps, and emits structured log lines (JSON) suitable for your log aggregator.

## Objectives

1. Propagate a trace id from the entrypoint through nested tool calls.
2. Log duration and outcome (success / error type) per tool.
3. Avoid logging secrets or full prompts — use safe previews only.

## Run the tests

```bash
pytest module-11-production/exercises/01-trace-middleware/test_start.py -v
```
