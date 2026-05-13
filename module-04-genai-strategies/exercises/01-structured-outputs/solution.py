"""
Exercise 01 — Structured Outputs (solution)
"""

from __future__ import annotations

import json
from typing import Literal

import openai
from pydantic import BaseModel


class MissionReport(BaseModel):
    mission_id: str
    status: Literal["active", "completed", "aborted"]
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str


SYSTEM_PROMPT = """\
You are a mission analyst for the DSS Pathfinder.
Given a free-text event description, return ONLY a JSON object matching this schema:
{
  "mission_id": "string — invent a short ID if none is given",
  "status": "active | completed | aborted",
  "risk_level": "low | medium | high | critical",
  "summary": "one-sentence summary of the event"
}
Do not include any text outside the JSON object.\
"""


def analyse(client: openai.OpenAI, text: str) -> MissionReport:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    return MissionReport.model_validate(data)


def main() -> None:
    client = openai.OpenAI()
    print("=== Mission Analyst — Structured Outputs ===")
    print("Describe a mission event. I'll return a structured report.")
    print("Type 'quit' to exit.\n")

    while True:
        text = input("Event> ").strip()
        if not text or text.lower() == "quit":
            break

        try:
            report = analyse(client, text)
            print(json.dumps(report.model_dump(), indent=2))
        except Exception as exc:
            print(f"Error: {exc}")
        print()


if __name__ == "__main__":
    main()
