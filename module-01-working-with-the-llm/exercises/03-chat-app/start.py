"""
Exercise 03 — Chat App
Add slash commands and file persistence to the streaming chat.

The streaming chat is provided (from Exercise 02's solution).
You only need to implement the persistence functions and command handler.
"""

import json
import sys
from pathlib import Path

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful and concise."
MODEL = "gpt-4o-mini"
DEFAULT_SAVE_PATH = Path("chat_history.json")


# ---------------------------------------------------------------------------
# Streaming chat (from Exercise 02 — already implemented)
# ---------------------------------------------------------------------------

def stream_response(client, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=MODEL, messages=messages, stream=True,
    )
    tokens = []
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            sys.stdout.write(content)
            sys.stdout.flush()
            tokens.append(content)
    print()
    return "".join(tokens)


# ---------------------------------------------------------------------------
# Persistence — YOUR CODE HERE
# ---------------------------------------------------------------------------

def save_session(filepath: Path, messages: list[dict]) -> None:
    """
    Write the messages list to a JSON file.
    Use json.dumps with indent=2 for readability.
    """
    # TODO: implement
    pass


def load_session(filepath: Path) -> list[dict]:
    """
    Read messages from a JSON file and return them.
    If the file does not exist, return a fresh session:
    [{"role": "system", "content": SYSTEM_PROMPT}]
    """
    # TODO: implement
    pass


# ---------------------------------------------------------------------------
# Command handler — YOUR CODE HERE
# ---------------------------------------------------------------------------

def handle_command(command: str, messages: list[dict], filepath: Path) -> list[dict] | None:
    """
    Process a slash command. Return the (possibly updated) messages list.
    Return None if the command is not recognised.

    Commands:
      /clear   — reset messages to [system prompt only]
      /history — print each message (role: content), return messages unchanged
      /save    — save messages to filepath, print confirmation
      /load    — load messages from filepath, print confirmation
      /help    — print available commands
    """
    # TODO: implement command handling
    pass


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def main(client, filepath: Path = DEFAULT_SAVE_PATH) -> None:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        if user_input.startswith("/"):
            result = handle_command(user_input, messages, filepath)
            if result is not None:
                messages = result
            else:
                print(f"Unknown command: {user_input}. Type /help for a list.\n")
            continue

        messages.append({"role": "user", "content": user_input})

        sys.stdout.write("\nAI: ")
        sys.stdout.flush()
        response = stream_response(client, messages)

        messages.append({"role": "assistant", "content": response})
        save_session(filepath, messages)
        print()


if __name__ == "__main__":
    from openai import OpenAI

    client = OpenAI()
    print("DSS Pathfinder AI (chat app) ready. Type a message or /help.\n")
    main(client)
