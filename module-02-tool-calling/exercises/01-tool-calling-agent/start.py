"""
Exercise 01 — Tool-Calling Agent
Build a tool-calling agent that makes real OpenAI API calls.
"""

import json
from dataclasses import dataclass, field
import os

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

# ---------------------------------------------------------------------------
# Tool schemas — tell the model what tools are available
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    # TODO: define 3 tools in the Responses API tool format:
    #   get_crew_count  — takes "department" (string), returns crew count
    #   get_ship_status — takes "system" (string), returns system status
    #   search_crew     — takes "query" (string), returns matching crew
    #
    # Each tool looks like:
    # {
    #     "type": "function",
    #     "name": "...",
    #     "description": "...",
    #     "parameters": {
    #         "type": "object",
    #         "properties": { ... },
    #         "required": [ ... ],
    #     },
    # }
]


# ---------------------------------------------------------------------------
# Tool handlers — the Python functions that actually do the work
# ---------------------------------------------------------------------------

CREW_DATA = {
    "command": [{"name": "Commander Elara Voss", "role": "Captain"}],
    "science": [
        {"name": "Dr. Jian Chen", "role": "Chief Science Officer"},
        {"name": "Ensign Dax Morel", "role": "Xenobiologist"},
        {"name": "Lt. Priya Sharma", "role": "Astrophysicist"},
    ],
    "engineering": [
        {"name": "Chief Engineer Mira Chen", "role": "Lead Engineer"},
        {"name": "Specialist Bodhi Kwan", "role": "Systems Tech"},
    ],
    "medical": [{"name": "Dr. Amara Osei", "role": "Chief Medical Officer"}],
}

SHIP_SYSTEMS = {
    "warp": {"system": "warp", "status": "online", "efficiency": 0.97},
    "shields": {"system": "shields", "status": "online", "efficiency": 0.85},
    "sensors": {"system": "sensors", "status": "degraded", "efficiency": 0.62},
    "life_support": {"system": "life_support", "status": "online", "efficiency": 0.99},
}


def get_crew_count(department: str) -> str:
    """Return the number of crew in a department."""
    # TODO: look up CREW_DATA[department], return JSON string with count
    pass


def get_ship_status(system: str) -> str:
    """Return the current status of a ship system."""
    # TODO: look up SHIP_SYSTEMS[system], return JSON string
    pass


def search_crew(query: str) -> str:
    """Search all crew by name or role."""
    # TODO: search across all departments, return matching crew as JSON
    pass


from collections.abc import Callable

TOOL_HANDLERS: dict[str, Callable[..., str]] = {
    "get_crew_count": get_crew_count,
    "get_ship_status": get_ship_status,
    "search_crew": search_crew,
}


# ---------------------------------------------------------------------------
# Agent result
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    final_answer: str | None
    tool_calls_made: list[str] = field(default_factory=list)
    steps: int = 0


# ---------------------------------------------------------------------------
# The agent loop
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Use your tools to answer crew and ship queries. Be concise."


def run_agent(client, question: str, max_steps: int = 5) -> AgentResult:
    """
    Run the tool-calling agent loop.

    1. Build messages: system prompt + user question.
    2. Call client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOLS).
    3. Collect calls = [item for item in response.output if item.type == "function_call"]:
       - If calls: add response.output to messages, then for each call run
         TOOL_HANDLERS[call.name](**json.loads(call.arguments)) and append
         {"type": "function_call_output", "call_id": call.call_id, "output": result}; loop.
       - Otherwise return response.output_text as the final answer.
    4. Stop after max_steps and return whatever you have.

    Return an AgentResult with the final answer, list of tool names called, and step count.
    """
    # TODO: implement the agent loop
    pass


# ---------------------------------------------------------------------------
# CLI chat loop
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI()
    print("DSS Pathfinder Agent ready. Type a question (or 'quit').\n")

    while True:
        q = input("You: ").strip()
        if not q or q.lower() in ("quit", "exit"):
            break
        result = run_agent(client, q)
        print(f"\nAgent: {result.final_answer}")
        if result.tool_calls_made:
            print(f"  (tools used: {', '.join(result.tool_calls_made)})")
        print()
