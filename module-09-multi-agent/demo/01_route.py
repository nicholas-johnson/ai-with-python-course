"""Part 1: One question, one department, one answer.
Run alone:  python module-09-multi-agent/demo/01_route.py
"""

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
        "You handle course plotting, stellar cartography, speed and heading, "
        "and hazard avoidance. Answer concisely in 2-3 sentences."
    ),
    "engineering": (
        "You are the Chief Engineer aboard the DSS Pathfinder. "
        "You handle reactor output, hull integrity, shields, and ship systems. "
        "Answer concisely in 2-3 sentences."
    ),
    "science": (
        "You are the Science Officer aboard the DSS Pathfinder. "
        "You handle sensor analysis, anomaly research, planetary surveys, "
        "and xenobiology. Answer concisely in 2-3 sentences."
    ),
}

QUESTION = "What is our current heading and ETA to Kepler-442b?"


class Route(BaseModel):
    department: Literal["navigation", "engineering", "science"]


def classify_query(query: str, client: OpenAI) -> str:
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Route,
        input=[
            {"role": "system", "content": "Classify the user query into exactly one department."},
            {"role": "user", "content": query},
        ],
    )
    route = response.output_parsed
    return route.department if route else "science"


def specialist_respond(department: str, query: str, client: OpenAI) -> str:
    prompt = SPECIALIST_PROMPTS[department]
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
    )
    return response.output_text


def demo_route(client: OpenAI):
    print("=" * 60)
    print("PART 1: ROUTE ONE QUESTION")
    print("=" * 60)
    print()

    department = classify_query(QUESTION, client)
    answer = specialist_respond(department, QUESTION, client)
    print(f"  Query:     {QUESTION}")
    print(f"  Routed to: {department}")
    print(f"  Response:  {answer}")
    print()


if __name__ == "__main__":
    demo_route(OpenAI())
