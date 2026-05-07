# Exercise 02 — Tool Registry

**Mission briefing:** The Pathfinder AI needs a registry where tools declare their schema (name, description, parameter spec) and the system can validate arguments, route calls to the right handler, and return structured errors when things go wrong.

## Objectives

1. Implement `ToolRegistry` with a `register(name, description, parameters)` decorator.
2. Implement `list_tools()` — returns the OpenAI-compatible tool list format.
3. Implement `call(name, arguments)` — validates the tool exists, calls the handler, catches errors.
4. Implement `validate_required(parameters_schema, arguments)` — check that all required fields are present.

## Run the tests

```bash
pytest module-02-agent-core/exercises/02-tool-registry/test_start.py -v
```
