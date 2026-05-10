# Exercise 04 — Multimodal Analysis

**Mission briefing:** The Pathfinder's hull cameras capture damage images and the bridge records audio logs. Build helpers that prepare **vision** and **audio** payloads for the LLM and parse the structured results.

## Objectives

1. Build a `prepare_image_message` function that wraps a base64-encoded image into the OpenAI vision message format.
2. Build a `prepare_audio_payload` that wraps raw audio bytes for transcription via the Whisper-style API.
3. Build a `parse_damage_report` function that extracts structured JSON from the model's vision response.

## Run the tests

```bash
pytest module-04-genai-strategies/exercises/04-multimodal-analysis/test_start.py -v
```
