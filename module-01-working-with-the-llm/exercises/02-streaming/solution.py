"""
Exercise 02 — Streaming Chat (solution)
"""

import os
import sys

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful and concise."
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def stream_response(client, messages: list[dict]) -> str:
    stream = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages, stream=True,
    )
    tokens = []
    for event in stream:
        if event.type == "response.output_text.delta":
            sys.stdout.write(event.delta)
            sys.stdout.flush()
            tokens.append(event.delta)
    print()
    return "".join(tokens)


def main(client) -> None:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        sys.stdout.write("\nAI: ")
        sys.stdout.flush()
        response = stream_response(client, messages)

        messages.append({"role": "assistant", "content": response})
        print()


if __name__ == "__main__":
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI()
    print("DSS Pathfinder AI (streaming) ready. Type a message (or 'quit').\n")
    main(client)
