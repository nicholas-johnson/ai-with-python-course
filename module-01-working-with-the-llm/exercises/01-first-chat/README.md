# Exercise 01 — First Chat

**Mission briefing:** Time to talk to the model. This is your Hello World moment with LLMs — make a real API call, get a response, then wrap it in an input loop so you can have a conversation.

## Objectives

1. Implement `chat(client, messages) -> str` — make a single `client.chat.completions.create()` call and return the response text.
2. Implement `main(client)` — an input loop that reads user input, calls `chat()`, and prints the response. Maintain the `messages` list so the model remembers the conversation.

## Try it

```bash
python start.py
```

Type a question, get a response. Try a follow-up — the model remembers what you said.

## Run the tests

```bash
pytest module-01-working-with-the-llm/exercises/01-first-chat/test_start.py -v
```
