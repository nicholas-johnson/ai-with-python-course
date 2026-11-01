"""Part 2: Router, specialist, then a critic that can send it back."""

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


class Route(BaseModel):
    department: Literal["navigation", "engineering", "science"]


class Review(BaseModel):
    approved: bool
    feedback: str


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
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {"role": "system", "content": SPECIALIST_PROMPTS[department]},
            {"role": "user", "content": query},
        ],
    )
    return response.output_text


def critic_review(query: str, answer: str, client: OpenAI) -> dict:
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Review,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a senior reviewer aboard the DSS Pathfinder. "
                    "Evaluate the specialist's answer for accuracy, completeness, "
                    "and safety. "
                    "Only reject if the answer is clearly wrong, dangerous, or incomplete."
                ),
            },
            {"role": "user", "content": f"QUERY: {query}\n\nSPECIALIST ANSWER: {answer}"},
        ],
    )
    review = response.output_parsed
    if review is None:
        return {"approved": True, "feedback": "Reviewer refused."}
    return review.model_dump()


def revise_answer(department: str, query: str, previous: str, feedback: str, client: OpenAI) -> str:
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {"role": "system", "content": SPECIALIST_PROMPTS[department]},
            {"role": "user", "content": query},
            {"role": "assistant", "content": previous},
            {
                "role": "user",
                "content": f"A reviewer rejected your answer: {feedback}\nPlease revise.",
            },
        ],
    )
    return response.output_text


def demo_critic(client: OpenAI):
    print("=" * 60)
    print("PART 2: SUPERVISOR-CRITIC")
    print("=" * 60)
    print()

    query = "What's the safest route through the asteroid field at sector 7G?"
    department = classify_query(query, client)
    answer = specialist_respond(department, query, client)
    print(f"  Query:       {query}")
    print(f"  Routed to:   {department}")
    print(f"  Draft:       {answer}\n")

    for attempt in range(1, 3):
        review = critic_review(query, answer, client)
        approved = review.get("approved", True)
        feedback = review.get("feedback", "")
        print(f"  Critic #{attempt}: {'APPROVED' if approved else 'REJECTED'}")
        print(f"  Feedback:    {feedback}\n")
        if approved:
            break
        answer = revise_answer(department, query, answer, feedback, client)
        print(f"  Revision:    {answer}\n")

    print(f"  Final answer: {answer}\n")
