# Exercise 03 — Session Manager

**Mission briefing:** Conversations disappear when the ship reboots — not acceptable. Build a pluggable session manager with two backends: in-memory (fast, ephemeral) and file-based (persistent). Both implement the same interface, so swapping is a one-line change.

## Objectives

1. Define `SessionBackend` Protocol: `load(session_id)`, `save(session_id, messages)`, `exists(session_id)`.
2. Implement `InMemoryBackend` — stores sessions in a dict.
3. Implement `FileBackend(directory)` — stores each session as a JSON file.
4. Implement `SessionManager(backend, system_prompt)` with `get_or_create`, `append`, and `list_sessions`.

## Run the tests

```bash
pytest module-03-chatbot/exercises/03-session-manager/test_start.py -v
```
