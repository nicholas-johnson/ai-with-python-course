"""Part 4: Three specialists vote. The tally picks the answer."""

import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

SPECIALIST_PROMPTS = {
    "navigation": (
        "You are the Navigation Officer aboard the DSS Pathfinder. "
        "Answer concisely in 2-3 sentences."
    ),
    "engineering": (
        "You are the Chief Engineer aboard the DSS Pathfinder. "
        "Answer concisely in 2-3 sentences."
    ),
    "science": (
        "You are the Science Officer aboard the DSS Pathfinder. "
        "Answer concisely in 2-3 sentences."
    ),
}


class Ballot(BaseModel):
    vote: Literal["reroute", "maintain course"]
    reasoning: str


def demo_consensus(client: OpenAI):
    print("=" * 60)
    print("PART 4: CONSENSUS")
    print("=" * 60)
    print()

    question = "Should we reroute to avoid the ion storm, or maintain course and reinforce shields?"
    options = ["reroute", "maintain course"]
    print(f"  Question: {question}")
    print(f"  Options:  {options}\n")

    votes: dict[str, str] = {}
    for department, prompt in SPECIALIST_PROMPTS.items():
        response = client.responses.parse(
            model=MODEL,
            reasoning={"effort": "none"},
            text_format=Ballot,
            input=[
                {
                    "role": "system",
                    "content": (
                        f"{prompt} Vote on the best course of action, with a brief rationale."
                    ),
                },
                {"role": "user", "content": question},
            ],
        )
        ballot = response.output_parsed
        vote = ballot.vote if ballot else options[0]
        reasoning = ballot.reasoning if ballot else "Abstained."
        votes[department] = vote
        print(f"  {department:>12}:  {vote}")
        print(f"               {reasoning}\n")

    tally: dict[str, int] = {}
    for vote in votes.values():
        tally[vote] = tally.get(vote, 0) + 1

    winner = max(tally, key=tally.get)
    print(f"  Tally:   {tally}")
    print(f"  Winner:  {winner}\n")
