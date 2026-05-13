"""
Demo: CLI chat loop — streaming conversation with real OpenAI API.
Run:  python module-01-working-with-the-llm/demo/01_chat_cli.py

Requires: OPENAI_API_KEY environment variable.
"""

import sys

from openai import OpenAI

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful, concise, and professional."
MODEL = "gpt-4o-mini"


def stream_response(client: OpenAI, messages: list[dict]) -> str:
    """Stream the LLM response, printing tokens as they arrive."""
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


def run_chat():
    client = OpenAI()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    print("\n=== DSS Pathfinder AI Console ===")
    print("Type your message. Enter 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("\nPathfinder AI signing off.")
            break

        messages.append({"role": "user", "content": user_input})

        sys.stdout.write("AI> ")
        sys.stdout.flush()
        response = stream_response(client, messages)

        messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    run_chat()
