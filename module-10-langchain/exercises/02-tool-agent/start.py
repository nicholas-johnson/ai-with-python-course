"""
Exercise 02 — Tool Agent (DSS Pathfinder)
Wrap ship tools as LangChain tools and run via AgentExecutor.

Run:  python start.py
Test: pytest test_start.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
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


# ---------------------------------------------------------------------------
# From Exercise 01 — classifier chain (complete)
# ---------------------------------------------------------------------------

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

_classify_model = ChatOpenAI(model=MODEL, temperature=0)
_classify_chain = _classify_prompt | _classify_model | JsonOutputParser()


def classify_report(report: str) -> dict:
    """Classify a crew report. Returns {category, summary, priority}."""
    return _classify_chain.invoke({"report": report})


# ---------------------------------------------------------------------------
# TODO: Define @tool functions
# ---------------------------------------------------------------------------

# from langchain_core.tools import tool
# from langchain.agents import create_tool_calling_agent, AgentExecutor

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
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are the DSS Pathfinder AI assistant. ..."),
#     ("placeholder", "{chat_history}"),
#     ("human", "{input}"),
#     ("placeholder", "{agent_scratchpad}"),
# ])
# model = ChatOpenAI(model=MODEL, temperature=0)
# agent = create_tool_calling_agent(model, tools, prompt)
# executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_agent(query: str) -> str:
    """Run the agent on a query. Returns the response string."""
    raise NotImplementedError("TODO: implement using executor.invoke()")


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
