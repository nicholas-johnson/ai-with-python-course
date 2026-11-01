"""Part 2: Responses API — one call, print the reply, return.
Run alone:  python module-01-working-with-the-llm/demo/02_responses.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
QUESTION = "In one sentence, why do spacecraft use radiators?"


def demo_responses(client: OpenAI):
    print("=" * 60)
    print("PART 2: RESPONSES API")
    print("=" * 60)
    print()

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        instructions="You are a helpful AI assistant. Be concise.",
        input=QUESTION,
    )
    print(response.output_text)
    print()


if __name__ == "__main__":
    demo_responses(OpenAI())
