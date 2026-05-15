"""
Exercise 02 — Tool Agent (solution)
Run:  python solution.py
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL = "gpt-4o-mini"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CREW = json.loads((PROJECT_ROOT / "data" / "crew.json").read_text())

SENSOR_DATA = {
    "hull_temperature": {"value": 272, "unit": "K", "status": "nominal"},
    "reactor_output": {"value": 94.2, "unit": "%", "status": "nominal"},
    "shield_integrity": {"value": 87, "unit": "%", "status": "warning"},
    "oxygen_level": {"value": 21.1, "unit": "%", "status": "nominal"},
    "radiation": {"value": 0.3, "unit": "mSv/h", "status": "nominal"},
}

# --- Classifier chain from Exercise 01 ---

_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary of the report,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])
_classify_chain = _classify_prompt | ChatOpenAI(model=MODEL, temperature=0) | JsonOutputParser()


def classify_report(report: str) -> dict:
    return _classify_chain.invoke({"report": report})


# --- Tools ---

@tool
def classify(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    return json.dumps(classify_report(report))


@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor. Available: hull_temperature, reactor_output, shield_integrity, oxygen_level, radiation."""
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

agent_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are the DSS Pathfinder AI assistant. "
     "Use your tools to help the crew. Do not guess — always use a tool when data is needed."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(ChatOpenAI(model=MODEL, temperature=0), tools, agent_prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_agent(query: str) -> str:
    return executor.invoke({"input": query})["output"]


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
