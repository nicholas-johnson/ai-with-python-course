"""
Exercise 01 — Structured Outputs
Get GPT to return reliable JSON. Validate with Pydantic.

Run:  python start.py
"""

from __future__ import annotations

import json
from typing import Literal

import openai
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# 1. Define the Pydantic model
# ---------------------------------------------------------------------------

class MissionReport(BaseModel):
    """Structured report returned by the LLM."""

    mission_id: str
    status: Literal["active", "completed", "aborted"]
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str


# ---------------------------------------------------------------------------
# 2. System prompt — constrains the model to return JSON matching the schema
# ---------------------------------------------------------------------------

# TODO: Write a system prompt that tells the model:
#   - Its role (mission analyst)
#   - The exact JSON schema it must return (matching MissionReport)
#   - That it must return ONLY valid JSON, no extra text
SYSTEM_PROMPT = ""


# ---------------------------------------------------------------------------
# 3. analyse() — single LLM call that returns a validated MissionReport
# ---------------------------------------------------------------------------

def analyse(client: openai.OpenAI, text: str) -> MissionReport:
    """Send *text* to the LLM and return a validated MissionReport.

    Requirements:
    - Use response_format={"type": "json_object"} to enforce JSON mode.
    - Parse the response content with json.loads, then validate with
      MissionReport.model_validate().
    - Use model="gpt-4o-mini" (cheap and fast for structured output).
    """
    # TODO: implement
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# 4. Interactive console loop
# ---------------------------------------------------------------------------

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
