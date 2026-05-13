# Exercise 03 — Chat App

**Mission briefing:** Your streaming chat works beautifully, but conversations vanish the moment you close the terminal. Turn the chat into a proper app with slash commands and file persistence — save conversations, load them back, clear history, and review what was said.

This exercise builds on Exercise 02. The streaming chat is already provided — you only need to implement the commands and persistence.

## Objectives

1. Implement `save_session(filepath, messages)` — write the messages list to a JSON file.
2. Implement `load_session(filepath) -> list[dict]` — read messages from a JSON file. Return a fresh session (system prompt only) if the file does not exist.
3. Implement `handle_command(command, messages, filepath) -> list[dict] | None` — process slash commands:
   - `/clear` — reset to system prompt only
   - `/history` — print all messages
   - `/save` — save to file
   - `/load` — load from file
   - `/help` — list available commands
   - Returns the (possibly updated) messages list, or None if the command is not recognised.
4. Wire command handling into the main loop — check for `/` prefix before sending to the LLM.

## Try it

```bash
python start.py
```

Chat, then type `/save` to persist. Close the app, restart, type `/load` to resume where you left off. Type `/help` to see all commands.

## Run the tests

```bash
pytest module-01-working-with-the-llm/exercises/03-chat-app/test_start.py -v
```
