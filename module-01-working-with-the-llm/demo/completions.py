"""Part 1: Chat Completions — one call, print the reply, return.
Run alone:  python module-01-working-with-the-llm/demo/completions.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
QUESTION = "In one sentence, why do spacecraft use radiators?"


def demo_completions(client: OpenAI):
    print("=" * 60)
    print("PART 1: CHAT COMPLETIONS")
    print("=" * 60)
    print()

    completion = client.chat.completions.create(
        model=MODEL,
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant. Be concise."},
            {"role": "user", "content": QUESTION},
        ],
    )
    print(completion.choices[0].message.content)
    print()


if __name__ == "__main__":
    demo_completions(OpenAI())
