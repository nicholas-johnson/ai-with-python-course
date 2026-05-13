# Exercise 03 -- Chat App

> Turn the streaming chat into a proper app with slash commands and file persistence -- save conversations, load them back, clear history, and review what was said.

## Recap

A good CLI chat needs two things beyond the basic loop: **persistence** so conversations survive restarts, and **commands** so users can manage their sessions.

**Persistence** is straightforward -- write the messages list to a JSON file and read it back:

```python
import json
from pathlib import Path

def save_session(filepath, messages):
    filepath.write_text(json.dumps(messages, indent=2))

def load_session(filepath):
    if not filepath.exists():
        return [{"role": "system", "content": SYSTEM_PROMPT}]
    return json.loads(filepath.read_text())
```

The key insight is that the entire conversation state is just a list of dicts. Serialise it as JSON and you can pick up exactly where you left off. In production you would use Redis or Postgres, but the pattern is the same -- save a list, load a list.

**Slash commands** give users control without sending text to the LLM. Prefix commands with `/` so they are easy to distinguish:

```python
if user_input.startswith("/"):
    handle_command(user_input, messages, filepath)
else:
    # send to LLM
```

The command handler checks the prefix and dispatches to the right action. It returns the (possibly modified) messages list, or `None` if the command is not recognised.

This exercise builds on Exercise 02. The streaming chat is already provided -- you only need to implement persistence and commands.

## What you build

- **`save_session(filepath, messages)`** -- write messages to a JSON file.
- **`load_session(filepath) -> list[dict]`** -- read messages from a JSON file (or return a fresh session if the file is missing).
- **`handle_command(command, messages, filepath) -> list[dict] | None`** -- dispatch slash commands.

The chat loop in `main()` is provided and already calls your functions.

## Step-by-step

### 1. Implement `save_session(filepath, messages)`

Write the messages list to the given filepath as JSON. Use `json.dumps(messages, indent=2)` for readability, then `filepath.write_text(...)`.

The tests check that the file is created and contains valid JSON matching the messages.

### 2. Implement `load_session(filepath) -> list[dict]`

If the file exists, read it with `filepath.read_text()` and parse with `json.loads()`. If the file does **not** exist, return a fresh session: `[{"role": "system", "content": SYSTEM_PROMPT}]`.

The tests check both the happy path (file exists) and the missing-file fallback.

### 3. Implement `handle_command(command, messages, filepath) -> list[dict] | None`

Handle these five commands:

| Command | Action |
| ------- | ------ |
| `/clear` | Reset messages to `[{"role": "system", "content": SYSTEM_PROMPT}]`. Print a confirmation. Return the new list. |
| `/history` | Print each message in the list (e.g. `role: content`). Return the unchanged list. |
| `/save` | Call `save_session(filepath, messages)`. Print a confirmation. Return the unchanged list. |
| `/load` | Call `load_session(filepath)`. Print a confirmation showing how many messages were loaded. Return the loaded list. |
| `/help` | Print a list of available commands. Return the unchanged list. |

If the command does not match any of these, return `None`. The chat loop already handles `None` by printing "Unknown command".

Strip the command string before comparing (e.g. `command.strip()`). Compare with `==` or use `.startswith()`.

The tests check that each command returns the correct messages list and that unrecognised commands return `None`.

## Try it

```bash
python start.py
```

Try this session:

1. Ask a couple of questions to build up conversation history.
2. Type `/history` -- you should see all the messages printed.
3. Type `/save` -- the conversation is written to `chat_history.json`.
4. Type `/clear` -- history is reset to just the system prompt.
5. Type `/load` -- the saved conversation is restored.
6. Close the app and restart it. Type `/load` to resume where you left off.
7. Type `/help` to see all commands.

## Tests

```bash
pytest module-01-working-with-the-llm/exercises/03-chat-app/test_start.py -v
```

## Stretch goals

1. Add a `/rename <name>` command that changes the save filepath, so users can manage multiple conversations.
2. Add a `/tokens` command that counts the total characters (or tokens, if you want to use `tiktoken`) in the conversation.
