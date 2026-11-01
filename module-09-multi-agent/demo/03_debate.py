"""Part 3: Two agents debate. A judge picks a winner."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def debate_round(topic: str, position: str, opponent_arg: str, client: OpenAI) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                f"You are a debate participant on the DSS Pathfinder. "
                f"Argue the '{position}' position on the given topic. "
                f"Be concise (2-3 sentences). If the opponent made an argument, "
                f"address it directly before making your own point."
            ),
        },
        {"role": "user", "content": f"Topic: {topic}"},
    ]
    if opponent_arg:
        messages.append({"role": "user", "content": f"Opponent's argument: {opponent_arg}"})
    response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
    return response.output_text


def judge_debate(
    topic: str, advocate_args: list[str], skeptic_args: list[str], client: OpenAI
) -> str:
    transcript = ""
    for i, (advocate, skeptic) in enumerate(zip(advocate_args, skeptic_args), 1):
        transcript += f"Round {i} — Advocate: {advocate}\nRound {i} — Skeptic: {skeptic}\n\n"
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "system",
                "content": (
                    "You are the Captain of the DSS Pathfinder acting as judge. "
                    "Read the debate transcript, weigh both sides, then declare "
                    "a winner (advocate or skeptic) with a brief rationale. "
                    "Keep your ruling to 3-4 sentences."
                ),
            },
            {"role": "user", "content": f"Topic: {topic}\n\n{transcript}"},
        ],
    )
    return response.output_text


def demo_debate(client: OpenAI):
    print("=" * 60)
    print("PART 3: DEBATE")
    print("=" * 60)
    print()

    topic = (
        "Should the DSS Pathfinder divert through the asteroid field "
        "to save 3 days of travel time?"
    )
    print(f"  Topic: {topic}\n")

    advocate_args: list[str] = []
    skeptic_args: list[str] = []

    for round_num in range(1, 3):
        print(f"  --- Round {round_num} ---")
        prev_skeptic = skeptic_args[-1] if skeptic_args else ""
        advocate = debate_round(topic, "advocate — in favour of diverting", prev_skeptic, client)
        advocate_args.append(advocate)
        print(f"  Advocate: {advocate}\n")

        skeptic = debate_round(topic, "skeptic — against diverting", advocate, client)
        skeptic_args.append(skeptic)
        print(f"  Skeptic:  {skeptic}\n")

    print(f"  Judge's ruling: {judge_debate(topic, advocate_args, skeptic_args, client)}\n")
