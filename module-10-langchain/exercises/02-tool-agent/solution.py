"""
Exercise 02 — Tool Agent (solution)
Run:  python solution.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
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

# --- Classifier chain from Exercise 01 ---

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
    return _classify_chain.invoke({"report": report}).model_dump()


# --- Tools ---

@tool
def classify(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    return json.dumps(classify_report(report))


@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor. Available: cargo_hold_pressure, main_drive_output, docking_seal_integrity, life_support_o2, background_radiation."""
    data = SENSOR_DATA.get(sensor_name)
    if not data:
        return json.dumps({"error": f"Unknown sensor '{sensor_name}'", "available": list(SENSOR_DATA.keys())})
    return json.dumps(data)


@tool
def query_crew(department: str) -> str:
    """Look up crew members by department. Departments: command, science, engineering, medical, operations, security."""
    results = [c for c in CREW if c["department"] == department]
    if not results:
        departments = sorted(set(c["department"] for c in CREW))
        return json.dumps({"error": f"No crew in '{department}'", "departments": departments})
    return json.dumps(results)


# --- Agent ---

tools = [classify, read_sensor, query_crew]

SYSTEM_PROMPT = (
    "You are the CSS Horizon AI assistant. "
    "Use your tools to help the crew. Do not guess — always use a tool when data is needed."
)

agent = create_agent(ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True), tools, system_prompt=SYSTEM_PROMPT)


def run_agent(query: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].text


def main():
    print("=" * 60)
    print("  EXERCISE 02 — TOOL AGENT")
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
        if user_input == "/tools":
            for t in tools:
                print(f"  {t.name}: {t.description}")
            print()
            continue
        try:
            print(f"\nAgent> {run_agent(user_input)}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


if __name__ == "__main__":
    main()
