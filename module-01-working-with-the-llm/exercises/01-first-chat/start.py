"""
Exercise 01 — First Chat
Make your first LLM API call, then build an interactive console chat.
"""

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful and concise."
MODEL = "gpt-4o-mini"


def chat(client, messages: list[dict]) -> str:
    """
    Send messages to the LLM and return the response text.

    1. Call client.chat.completions.create(model=MODEL, messages=messages).
    2. Extract the text from response.choices[0].message.content.
    3. Return it.
    """
    # TODO: implement
    pass


def main(client) -> None:
    """
    Interactive console chat loop.

    1. Start with a messages list containing the system prompt.
    2. Read user input with input("You: ").
    3. If the user types "quit" or "exit", break.
    4. Append the user message to messages.
    5. Call chat(client, messages) to get the response.
    6. Append the assistant message to messages.
    7. Print the response.
    8. Repeat.
    """
    # TODO: implement
    pass


if __name__ == "__main__":
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI()
    print("DSS Pathfinder AI ready. Type a message (or 'quit').\n")
    main(client)
