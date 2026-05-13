# Exercise 03 — Multimodal API

**Goal:** Build a FastAPI app that exposes chat, vision, and audio transcription as API endpoints. This is the Day 1 closer -- the instructor will provide a web frontend that talks to your API.

## What you build

1. `POST /chat` — accepts `{"text": "..."}`, returns a structured `MissionReport` JSON (from Exercise 01).
2. `POST /vision` — accepts `{"image": "<base64>"}` or `{"image_url": "https://..."}`, returns a structured `MissionReport` (from Exercise 02).
3. `POST /transcribe` — accepts an audio file upload, transcribes it with Whisper, returns `{"transcript": "..."}`.
4. `GET /health` — returns `{"status": "ok"}`.

## Run it

```bash
python start.py
# Server starts on http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Run the tests

```bash
pytest module-04-genai-strategies/exercises/03-multimodal-api/test_start.py -v
```
