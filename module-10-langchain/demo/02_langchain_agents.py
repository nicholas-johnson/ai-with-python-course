"""
Demo 2: LangChain Agents — @tool decorator, AgentExecutor, and the tool-calling loop.
Run:  python module-10-langchain/demo/02_langchain_agents.py

DSS Pathfinder: build a tool agent that reads sensors, classifies reports, and queries crew.

Part 1: Define tools — @tool decorator and schema generation
Part 2: Build and run the agent — AgentExecutor with verbose trace
Part 3: Interactive — ask the agent anything

Requires: OPENAI_API_KEY environment variable.
"""

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
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CREW = json.loads((PROJECT_ROOT / "data" / "crew.json").read_text())

SENSOR_DATA = {
    "hull_temperature": {"value": 272, "unit": "K", "status": "nominal"},
    "reactor_output": {"value": 94.2, "unit": "%", "status": "nominal"},
    "shield_integrity": {"value": 87, "unit": "%", "status": "warning"},
    "oxygen_level": {"value": 21.1, "unit": "%", "status": "nominal"},
    "radiation": {"value": 0.3, "unit": "mSv/h", "status": "nominal"},
}


# ---------------------------------------------------------------------------
# Classifier chain (from demo 01)
# ---------------------------------------------------------------------------

_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])
_classify_model = ChatOpenAI(model=MODEL, temperature=0)
_classify_chain = _classify_prompt | _classify_model | JsonOutputParser()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def classify_report(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    result = _classify_chain.invoke({"report": report})
    return json.dumps(result)


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


tools = [classify_report, read_sensor, query_crew]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are the DSS Pathfinder AI assistant. "
     "Use your tools to help the crew. Do not guess — always use a tool when data is needed."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

model = ChatOpenAI(model=MODEL, temperature=0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pause():
    try:
        input("\n  [Press Enter to continue...]\n")
    except (EOFError, KeyboardInterrupt):
        print()


# ---------------------------------------------------------------------------
# Part 1: Define tools
# ---------------------------------------------------------------------------

def demo_tools():
    print("=" * 60)
    print("PART 1: DEFINE TOOLS")
    print("=" * 60)

    print("\n  The @tool decorator generates a schema from type hints + docstring.\n")

    for t in tools:
        print(f"  Tool: {t.name}")
        print(f"    Description: {t.description}")
        schema = t.args_schema.schema() if t.args_schema else {}
        print(f"    Schema: {json.dumps(schema.get('properties', {}), indent=6)}")
        print()

    print("  This is exactly what you built by hand in Module 2 —")
    print("  LangChain just automates the schema generation.")

    pause()


# ---------------------------------------------------------------------------
# Part 2: Build and run the agent
# ---------------------------------------------------------------------------

def demo_agent():
    print("=" * 60)
    print("PART 2: BUILD AND RUN THE AGENT")
    print("=" * 60)

    agent = create_tool_calling_agent(model, tools, agent_prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    queries = [
        "What is the current shield integrity?",
        "Classify this report: Plasma conduit 7-B ruptured during warp — coolant leak in engineering.",
    ]

    for q in queries:
        print(f"\n  Query: {q}\n")
        result = executor.invoke({"input": q})
        print(f"\n  Final answer: {result['output']}")
        pause()


# ---------------------------------------------------------------------------
# Part 3: Interactive
# ---------------------------------------------------------------------------

def demo_interactive():
    print("=" * 60)
    print("PART 3: INTERACTIVE")
    print("=" * 60)

    agent = create_tool_calling_agent(model, tools, agent_prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print("\nAsk the agent anything. It can read sensors, classify reports, and query crew.")
    print("Commands: /tools, quit\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break

        if user_input == "/tools":
            for t in tools:
                print(f"  {t.name}: {t.description}")
            print()
            continue

        try:
            result = executor.invoke({"input": user_input})
            print(f"\nAgent> {result['output']}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Define tools",           demo_tools),
    "2": ("Build and run the agent", demo_agent),
    "3": ("Interactive",             demo_interactive),
}


def main():
    print("\n" + "=" * 60)
    print("  DEMO 2 — LANGCHAIN AGENTS")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("RECAP")
    print("=" * 60)
    print()
    print("  @tool          — schema from type hints + docstring")
    print("  AgentExecutor  — runs the tool-calling loop for you")
    print("  verbose=True   — shows the full thought/action/observation trace")
    print("=" * 60)


if __name__ == "__main__":
    main()
