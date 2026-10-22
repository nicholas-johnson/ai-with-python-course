"""
Demo 2: LangChain Agents — @tool decorator, create_agent, middleware, and memory.
Run:  python module-10-langchain/demo/02_langchain_agents.py

DSS Pathfinder: build a tool agent that reads sensors, classifies reports, and queries crew.

Part 1: Define tools — @tool decorator and schema generation
Part 2: Build and run the agent — create_agent with a step-by-step trace
Part 3: Middleware — hook into every tool call; cap runaway loops
Part 4: Memory — a checkpointer keeps the conversation per thread_id
Part 5: Interactive — ask the agent anything (middleware + memory)

Requires: OPENAI_API_KEY environment variable.
"""

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware, wrap_tool_call
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
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

class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])
_classify_model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)
_classify_chain = _classify_prompt | _classify_model.with_structured_output(Classification)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def classify_report(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    result = _classify_chain.invoke({"report": report})
    return result.model_dump_json()


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

SYSTEM_PROMPT = (
    "You are the DSS Pathfinder AI assistant. "
    "Use your tools to help the crew. Do not guess — always use a tool when data is needed."
)

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

@wrap_tool_call
def log_tool_calls(request, handler):
    """Print every tool call and its result as the agent runs."""
    call = request.tool_call
    print(f"  → {call['name']}({json.dumps(call['args'])})")
    result = handler(request)
    print(f"  ← {str(result.content)[:200]}")
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_trace(messages):
    """Show each step of the tool-calling loop: tool calls, tool results, final answer."""
    for msg in messages:
        if msg.type == "ai" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"  → {call['name']}({json.dumps(call['args'])})")
        elif msg.type == "tool":
            print(f"  ← {msg.content[:200]}")


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
        schema = t.args_schema.model_json_schema() if t.args_schema else {}
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

    agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT)

    queries = [
        "What is the current shield integrity?",
        "Classify this report: Plasma conduit 7-B ruptured during warp — coolant leak in engineering.",
    ]

    for q in queries:
        print(f"\n  Query: {q}\n")
        result = agent.invoke({"messages": [{"role": "user", "content": q}]})
        print_trace(result["messages"])
        print(f"\n  Final answer: {result['messages'][-1].text}")
        pause()


# ---------------------------------------------------------------------------
# Part 3: Middleware
# ---------------------------------------------------------------------------

def demo_middleware():
    print("=" * 60)
    print("PART 3: MIDDLEWARE")
    print("=" * 60)

    print("\n  Middleware wraps steps of the agent loop. Two here:")
    print("    @wrap_tool_call log_tool_calls  — runs around every tool call")
    print("    ToolCallLimitMiddleware(run_limit=4) — stops a runaway loop\n")
    print("  Built-ins also cover human approval, PII redaction, retries,")
    print("  model fallback, and summarising long conversations.\n")

    agent = create_agent(
        model,
        tools,
        system_prompt=SYSTEM_PROMPT,
        middleware=[log_tool_calls, ToolCallLimitMiddleware(run_limit=4)],
    )

    q = "Check shield integrity and radiation, then list the engineering crew."
    print(f"  Query: {q}\n")
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    print(f"\n  Final answer: {result['messages'][-1].text}")
    pause()


# ---------------------------------------------------------------------------
# Part 4: Memory
# ---------------------------------------------------------------------------

def demo_memory():
    print("=" * 60)
    print("PART 4: MEMORY WITH A CHECKPOINTER")
    print("=" * 60)

    print("\n  create_agent(..., checkpointer=InMemorySaver()) saves the agent's state")
    print("  after every step. Calls with the same thread_id continue the conversation.\n")

    agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver())

    turns = [
        ("bridge", "Note for the log: Lt. Okafor is leading the away team to Kepler-442b."),
        ("bridge", "Who is leading the away team?"),
        ("medbay", "Who is leading the away team?"),
    ]
    for thread_id, q in turns:
        config = {"configurable": {"thread_id": thread_id}}
        result = agent.invoke({"messages": [{"role": "user", "content": q}]}, config)
        print(f"  [{thread_id}] You> {q}")
        print(f"  [{thread_id}] Agent> {result['messages'][-1].text}\n")

    print("  The 'medbay' thread has its own (empty) history and never saw the note,")
    print("  so whatever it answers is a guess from its tools — not Okafor.")
    print("  Swap InMemorySaver for a SQLite or Postgres checkpointer to persist it.")
    pause()


# ---------------------------------------------------------------------------
# Part 5: Interactive
# ---------------------------------------------------------------------------

def demo_interactive():
    print("=" * 60)
    print("PART 5: INTERACTIVE")
    print("=" * 60)

    agent = create_agent(
        model,
        tools,
        system_prompt=SYSTEM_PROMPT,
        middleware=[log_tool_calls, ToolCallLimitMiddleware(run_limit=6)],
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "interactive"}}

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
            result = agent.invoke({"messages": [{"role": "user", "content": user_input}]}, config)
            print(f"\nAgent> {result['messages'][-1].text}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Define tools",           demo_tools),
    "2": ("Build and run the agent", demo_agent),
    "3": ("Middleware",              demo_middleware),
    "4": ("Memory",                  demo_memory),
    "5": ("Interactive",             demo_interactive),
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
    print("  create_agent   — runs the tool-calling loop for you (built on LangGraph)")
    print("  messages       — the result holds every tool call and tool result")
    print("  middleware=[]  — hook into the loop: logging, limits, approval, PII")
    print("  checkpointer   — conversation memory per thread_id")
    print("=" * 60)


if __name__ == "__main__":
    main()
