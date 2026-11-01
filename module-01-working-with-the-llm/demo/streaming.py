"""Part 4: Streaming — tokens arrive one by one, perceived latency drops."""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SYSTEM_PROMPT = "You are a helpful AI assistant. Be concise and professional."


def stream_response(client: OpenAI, messages: list[dict]) -> str:
    """Stream the response token by token, printing as they arrive."""
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


def demo_streaming(client: OpenAI):
    print("=" * 60)
    print("PART 4: STREAMING")
    print("=" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("\nWith stream=True, the API sends a series of typed events.")
    print("Text arrives in 'response.output_text.delta' events; the rest mark progress.")
    print("Type your messages below. Type 'quit' to return to the menu.\n")

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})

        stream = client.responses.create(
            model=MODEL, reasoning={"effort": "none"}, input=messages, stream=True,
        )
        tokens = []
        event_num = 0
        print("\n--- Events arriving ---")
        for event in stream:
            delta = event.delta if event.type == "response.output_text.delta" else None
            print(f"  event {event_num}: {event.type}  delta={delta!r}")
            event_num += 1
            if delta:
                tokens.append(delta)

        full_response = "".join(tokens)
        print(f"\n--- Assembled response ({event_num} events, {len(tokens)} text deltas) ---")
        print(f"AI>  {full_response}\n")
        messages.append({"role": "assistant", "content": full_response})


def demo_streaming_clean(client: OpenAI):
    print("=" * 60)
    print("PART 4b: STREAMING (CLEAN)")
    print("=" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("\nSame streaming, but just the nice output — no chunk logging.")
    print("Type your messages below. Type 'quit' to return to the menu.\n")

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        sys.stdout.write("AI>  ")
        sys.stdout.flush()
        response = stream_response(client, messages)
        messages.append({"role": "assistant", "content": response})
        print()
