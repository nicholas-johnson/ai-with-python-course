# Exercise 02 — Tool Registry

**Mission briefing:** Your tool-calling agent works, but those hand-written JSON schemas are tedious and error-prone. Build a `ToolRegistry` class that lets you register tools with a decorator, auto-generates the OpenAI tool list, and routes calls to the right handler with error handling.

This exercise builds on Exercise 01. The agent loop and data are already provided — you only need to implement the registry.

## Objectives

1. Implement `ToolRegistry` with a `register(name, description, parameters)` decorator.
2. Implement `list_tools()` — returns the OpenAI-compatible tool list.
3. Implement `execute(name, arguments)` — validates the tool exists, calls the handler, catches errors, returns a string result.
4. Register the ship tools using the decorator and wire the registry into the agent loop.

## Try it

```bash
python start.py
```

Same agent, cleaner code. Ask the same questions as Exercise 01 — the behaviour should be identical.

## Run the tests

```bash
pytest module-02-agent-core/exercises/02-tool-registry/test_start.py -v
```
