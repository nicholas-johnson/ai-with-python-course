"""Part 3: Summarise a conversation into a few sentences."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

CONVERSATION = [
    {"role": "user", "content": "I need a full status report on all ship systems."},
    {
        "role": "assistant",
        "content": (
            "Reactor: 98% efficiency. Navigation: Online, course locked to Kepler-442b. "
            "Life support: Nominal. Shields: 85% charge."
        ),
    },
    {"role": "user", "content": "Why are shields below 100%?"},
    {
        "role": "assistant",
        "content": (
            "The ion storm on stardate 2287.3 depleted shield reserves. "
            "Recharge rate is 2% per hour — full charge expected in 7.5 hours."
        ),
    },
    {"role": "user", "content": "Prioritise shield recharge. Divert auxiliary power."},
    {
        "role": "assistant",
        "content": (
            "Acknowledged. Diverting auxiliary power to shields. "
            "New recharge rate: 5% per hour. Full charge in 3 hours."
        ),
    },
    {"role": "user", "content": "What about the sensor array maintenance scheduled for tomorrow?"},
    {
        "role": "assistant",
        "content": (
            "Sensor array maintenance is scheduled for 0800 tomorrow. "
            "It requires 2 hours downtime. Recommend completing before shield recharge finishes."
        ),
    },
]


def summarise_turns(turns: list[dict], client: OpenAI) -> str:
    formatted = "\n".join(f"{turn['role']}: {turn['content']}" for turn in turns)
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "system",
                "content": (
                    "Summarise the following conversation in 2-3 sentences. "
                    "Preserve key facts, decisions, and any action items."
                ),
            },
            {"role": "user", "content": formatted},
        ],
    )
    return response.output_text


def demo_summarise(client: OpenAI):
    print("=" * 60)
    print("PART 3: SUMMARISATION")
    print("=" * 60)
    print()

    total_chars = sum(len(message["content"]) for message in CONVERSATION)
    print(f"  Original conversation: {len(CONVERSATION)} messages, {total_chars} characters\n")

    summary = summarise_turns(CONVERSATION, client)
    print(f"  Summary ({len(summary)} chars):")
    print(f"  {summary}")
    print(f"\n  Compression ratio: {len(summary)}/{total_chars} = {len(summary) / total_chars:.0%}")
    print()


if __name__ == "__main__":
    demo_summarise(OpenAI())
