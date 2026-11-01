"""Part 3: The chat loop — message roles, and the list the model sees every call."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SYSTEM_PROMPT = "You are a helpful AI assistant. Be concise and professional."


def chat(client: OpenAI, messages: list[dict]) -> str:
    """Non-streaming single-shot call. Returns the response text."""
    response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
    return response.output_text


def demo_basic_chat(client: OpenAI):
    print("=" * 60)
    print("PART 3: THE CHAT LOOP")
    print("=" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("\nThe message list starts with one system message.")
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

        print(f"\n--- Sending {len(messages)} messages to the API ---")
        for i, m in enumerate(messages):
            role = m["role"].upper()
            text = m["content"]
            if len(text) > 120:
                text = text[:120] + "..."
            print(f"  [{i}] {role}: {text}")
        print()

        response = chat(client, messages)
        messages.append({"role": "assistant", "content": response})
        print(f"AI>  {response}\n")

    print(f"\nMessages list ended with {len(messages)} entries.")
    print("The model sees the full list every call — that's how it 'remembers'.\n")
