"""
Exercise 01 — First Chat (solution)
"""

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful and concise."
MODEL = "gpt-4o-mini"


def chat(client, messages: list[dict]) -> str:
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content


def main(client) -> None:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})
        response = chat(client, messages)
        messages.append({"role": "assistant", "content": response})
        print(f"\nAI: {response}\n")


if __name__ == "__main__":
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI()
    print("DSS Pathfinder AI ready. Type a message (or 'quit').\n")
    main(client)
