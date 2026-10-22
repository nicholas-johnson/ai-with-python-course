"""Specialist agents — provided from Exercise 01 solution."""
from __future__ import annotations
import os
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DEPARTMENTS = ["medical", "tactical", "comms"]


class Route(BaseModel):
    department: Literal["medical", "tactical", "comms"]

SPECIALIST_PROMPTS = {
    "medical": (
        "You are the Medical Officer aboard the DSS Pathfinder. "
        "You handle all questions about crew health, injuries, quarantine "
        "protocols, radiation exposure, and bio-hazard containment. "
        "Answer concisely with clinical precision."
    ),
    "tactical": (
        "You are the Tactical Officer aboard the DSS Pathfinder. "
        "You handle all questions about threat assessment, shields, "
        "weapons systems, evasive maneuvers, and defense protocols. "
        "Answer concisely and with authority."
    ),
    "comms": (
        "You are the Communications Officer aboard the DSS Pathfinder. "
        "You handle all questions about hailing frequencies, signal "
        "decryption, subspace relays, distress beacons, and encrypted "
        "transmissions. Answer concisely and cite signal data where possible."
    ),
}


def classify_query(query: str, client: OpenAI) -> str:
    response = client.chat.completions.parse(
        model=MODEL,
        reasoning_effort="none",
        response_format=Route,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a query router for a starship crew. "
                    "Classify the user's message into exactly one department. "
                    "Valid departments: medical, tactical, comms. "
                    "medical = injuries, health, quarantine, radiation, bio-hazards. "
                    "tactical = threats, shields, weapons, evasive maneuvers, defense. "
                    "comms = hailing, signals, subspace relays, beacons, encryption. "
                    "If unsure, pick the closest match."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    route = response.choices[0].message.parsed
    return route.department if route else "medical"


def specialist_agent(department: str, query: str, client: OpenAI) -> str:
    system_prompt = SPECIALIST_PROMPTS.get(department, SPECIALIST_PROMPTS["medical"])
    response = client.chat.completions.create(
        model=MODEL,
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content


def route_and_respond(query: str, client: OpenAI) -> dict:
    department = classify_query(query, client)
    response = specialist_agent(department, query, client)
    return {"department": department, "response": response}
