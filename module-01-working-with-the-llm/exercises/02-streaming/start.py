"""
Exercise 02 — Streaming Chat
Upgrade the chat to stream responses token by token.

The basic chat function and input loop are provided (from Exercise 01's solution).
You only need to implement stream_response().
"""

import os
import sys

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful and concise."
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


# ---------------------------------------------------------------------------
# Basic chat (from Exercise 01 — already implemented)
# ---------------------------------------------------------------------------

def chat(client, messages: list[dict]) -> str:
    """Non-streaming chat — kept for reference."""
    response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
    return response.output_text


# ---------------------------------------------------------------------------
# Streaming — YOUR CODE HERE
# ---------------------------------------------------------------------------

def stream_response(client, messages: list[dict]) -> str:
    """
    Stream the LLM response token by token.

    1. Call client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, stream=True).
    2. Iterate over the stream. Each item is an event with a .type.
    3. Text arrives in events where event.type == "response.output_text.delta";
       the token is event.delta. Skip every other event type (they mark
       progress: response.created, response.completed, ...).
    4. Print each token immediately (sys.stdout.write + flush, no newline).
    5. Collect all tokens into a list.
    6. After the loop, print a newline.
    7. Return the full text (joined tokens).
    """
    # TODO: implement streaming
    pass


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

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
