# Exercise 02 — Test and extend

**Mission briefing:** Harden the capstone with integration tests (happy path + one failure mode) and write a short extension checklist for new tools, indexes, and agent roles.

## Objectives

1. Add at least one integration test that exercises RAG or tool calling without mocks for the whole universe (local stubs OK).
2. Document extension points: where to register tools, add indexes, change prompts, and plug policies.
3. Capture how to run the full stack locally (commands, env vars, ports).

## Run the tests

```bash
pytest module-12-capstone/exercises/02-test-and-extend/test_start.py -v
```
