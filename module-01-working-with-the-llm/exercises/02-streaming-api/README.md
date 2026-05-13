# Exercise 02 — Streaming API

**Mission briefing:** Bridge officers need a web API that streams AI responses in real time — not a single JSON blob after a long wait. Build a FastAPI endpoint that accepts a chat message and streams tokens back via Server-Sent Events.

## Objectives

1. Implement `create_app()` returning a FastAPI app.
2. `POST /chat` — accepts `{"message": "...", "session_id": "..."}`, returns an SSE stream.
3. The stream emits: `session` event (with session_id), then `token` events, then `done` event.
4. `GET /sessions/{session_id}` — returns the stored message history.

## Run the tests

```bash
pytest module-01-working-with-the-llm/exercises/02-streaming-api/test_start.py -v
```
