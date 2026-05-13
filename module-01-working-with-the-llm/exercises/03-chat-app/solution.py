"""
Exercise 03 — Chat App (solution)
"""

import json
import sys
from pathlib import Path

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful and concise."
MODEL = "gpt-4o-mini"
DEFAULT_SAVE_PATH = Path("chat_history.json")


# ---------------------------------------------------------------------------
# Streaming chat (from Exercise 02)
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
# Persistence
# ---------------------------------------------------------------------------

def save_session(filepath: Path, messages: list[dict]) -> None:
    filepath.write_text(json.dumps(messages, indent=2))


def load_session(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return [{"role": "system", "content": SYSTEM_PROMPT}]
    return json.loads(filepath.read_text())


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------

def handle_command(command: str, messages: list[dict], filepath: Path) -> list[dict] | None:
    cmd = command.strip().lower()

    if cmd == "/clear":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("History cleared.\n")
        return messages

    if cmd == "/history":
        for msg in messages:
            print(f"  [{msg['role']}] {msg.get('content', '')}")
        print()
        return messages

    if cmd == "/save":
        save_session(filepath, messages)
        print(f"Session saved to {filepath}.\n")
        return messages

    if cmd == "/load":
        messages = load_session(filepath)
        count = len(messages) - 1
        print(f"Session loaded from {filepath} ({count} messages).\n")
        return messages

    if cmd == "/help":
        print("Commands:")
        print("  /clear   — reset conversation")
        print("  /history — show all messages")
        print("  /save    — save conversation to file")
        print("  /load    — load conversation from file")
        print("  /help    — show this help")
        print()
        return messages

    return None


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
