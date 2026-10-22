"""
Exercise 02 — Tool Agent (CSS Horizon)
Wrap ship tools as LangChain tools and run them with create_agent.

Run:  python start.py
Test: pytest test_start.py -v
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
EXERCISE_DATA = Path(__file__).resolve().parents[1] / "data"
CREW = json.loads((EXERCISE_DATA / "horizon_crew.json").read_text())

SENSOR_DATA = {
    "cargo_hold_pressure": {"value": 101.2, "unit": "kPa", "status": "nominal"},
    "main_drive_output": {"value": 96.0, "unit": "%", "status": "nominal"},
    "docking_seal_integrity": {"value": 94.0, "unit": "%", "status": "nominal"},
    "life_support_o2": {"value": 20.9, "unit": "%", "status": "nominal"},
    "background_radiation": {"value": 0.12, "unit": "mSv/h", "status": "nominal"},
}


# ---------------------------------------------------------------------------
# From Exercise 01 — classifier chain (complete)
# ---------------------------------------------------------------------------

class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the CSS Horizon.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])
_classify_model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)
_classify_chain = _classify_prompt | _classify_model.with_structured_output(Classification)


def classify_report(report: str) -> dict:
    """Classify a crew report. Returns {category, summary, priority}."""
    return _classify_chain.invoke({"report": report}).model_dump()


# ---------------------------------------------------------------------------
# TODO: Define @tool functions
# ---------------------------------------------------------------------------

# from langchain_core.tools import tool
# from langchain.agents import create_agent

# @tool
# def classify(report: str) -> str:
#     """Classify a crew report into category, summary, and priority."""
#     result = classify_report(report)
#     return json.dumps(result)

# @tool
# def read_sensor(sensor_name: str) -> str:
#     """Read the current value of a ship sensor."""
#     ...

# @tool
# def query_crew(department: str) -> str:
#     """Look up crew members by department."""
#     ...


# ---------------------------------------------------------------------------
# TODO: Build the agent
# ---------------------------------------------------------------------------

# tools = [classify, read_sensor, query_crew]
# SYSTEM_PROMPT = "You are the CSS Horizon AI assistant. ..."
# model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)
# agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT)


def run_agent(query: str) -> str:
    """Run the agent on a query. Returns the response string."""
    # Hint: agent.invoke({"messages": [{"role": "user", "content": query}]})
    #       returns {"messages": [...]} — the last message is the answer.
    raise NotImplementedError("TODO: implement using agent.invoke()")


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  EXERCISE 02 — TOOL AGENT")
    print("  LangChain agent with ship tools")
    print("=" * 60)

    print("\nAvailable sensors:", ", ".join(SENSOR_DATA.keys()))
    print("Commands: /tools, /sensors, quit\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break

        if user_input == "/sensors":
            for name, data in SENSOR_DATA.items():
                print(f"  {name}: {data['value']} {data['unit']} ({data['status']})")
            print()
            continue

        # TODO: handle /tools command

        try:
            response = run_agent(user_input)
            print(f"\nAgent> {response}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


if __name__ == "__main__":
    main()
