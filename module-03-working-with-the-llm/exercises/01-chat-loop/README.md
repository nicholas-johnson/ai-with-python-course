# Exercise 01 — Chat Loop

**Mission briefing:** Build the Pathfinder's conversational interface. The chat loop maintains history, sends messages to an LLM (mock), and collects the streamed response. It supports a `/clear` command to reset history and `/history` to show the conversation so far.

## Objectives

1. Implement `ChatBot(llm, system_prompt)` with a `messages` history list.
2. Implement `chat(user_input)` — appends user message, calls the LLM, collects response, appends assistant message, returns the full response text.
3. Implement `clear()` — resets to just the system message.
4. Implement `get_history()` — returns the messages list.

## Run the tests

```bash
pytest module-03-chatbot/exercises/01-chat-loop/test_start.py -v
```
