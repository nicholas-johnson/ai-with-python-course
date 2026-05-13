# Exercise 02 — Streaming Chat

**Mission briefing:** Your chatbot works, but the crew stares at a blank screen for seconds while the model generates a response. Upgrade the chat to stream tokens as they arrive — words flow in real time and perceived latency drops from seconds to milliseconds.

This exercise builds on Exercise 01. The chat function and input loop are already provided — you only need to implement streaming.

## Objectives

1. Implement `stream_response(client, messages) -> str` — call the API with `stream=True`, print each token as it arrives, return the assembled full text.
2. Wire `stream_response` into the chat loop (replace the `chat()` call).

## Try it

```bash
python start.py
```

Same chat, but now words appear as the model generates them. Try a longer question to see the difference.

## Run the tests

```bash
pytest module-01-working-with-the-llm/exercises/02-streaming/test_start.py -v
```
