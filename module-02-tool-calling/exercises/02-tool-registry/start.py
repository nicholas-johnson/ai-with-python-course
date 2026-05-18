"""
Exercise 02 — Auto-Schema Tool Registry
Build a ToolRegistry that auto-generates OpenAI-compatible JSON schemas from
Python type hints, then wire it into a planetary exploration agent.

The agent loop and planet data are provided.
You need to implement the ToolRegistry class and register the tools.
"""

import inspect
import json
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Type mapping: Python types → JSON Schema types (provided for you)
# ---------------------------------------------------------------------------

TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

# ---------------------------------------------------------------------------
# Planetary data
# ---------------------------------------------------------------------------

PLANET_DB = {
    "KEP-442b": {
        "name": "KEP-442b",
        "atmosphere": "nitrogen-oxygen",
        "gravity": 1.3,
        "hazards": ["seismic activity"],
        "distance_ly": 1206,
    },
    "PROX-b": {
        "name": "PROX-b",
        "atmosphere": "carbon-dioxide",
        "gravity": 1.1,
        "hazards": ["radiation"],
        "distance_ly": 4.2,
    },
    "TRAP-1e": {
        "name": "TRAP-1e",
        "atmosphere": "nitrogen-oxygen",
        "gravity": 0.9,
        "hazards": [],
        "distance_ly": 39,
    },
}

MISSION_LOG: list[dict] = []


# ---------------------------------------------------------------------------
# ToolRegistry — YOUR CODE HERE
# ---------------------------------------------------------------------------


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, description: str):
        """Decorator that registers a function as a tool.

        Unlike the demo's registry (which takes name + description + a hand-written
        JSON schema), this one only takes a description.  Everything else is
        inferred automatically:

        - The **tool name** comes from fn.__name__.
        - The **JSON schema** is built by inspecting the function signature.

        Hint: use inspect.signature(fn) to iterate over parameters.  Each
        parameter has a .name and .annotation (the type hint).  Use TYPE_MAP
        to convert Python types to JSON Schema types.  Parameters without a
        default value are "required".
        """
        # TODO: return a decorator that:
        #   1. Calls inspect.signature(fn) to get the parameter list
        #   2. Builds {"type": "object", "properties": {...}, "required": [...]}
        #   3. Stores the tool in self._tools[fn.__name__]
        #   4. Returns fn unchanged
        pass

    def list_tools(self) -> list[dict]:
        """Return tools in OpenAI-compatible format:

        [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
        """
        # TODO: build and return the tool list from self._tools
        pass

    def execute(self, name: str, arguments: dict) -> str:
        """Look up the tool by name and call its handler with the arguments.

        Error handling:
        - Unknown tool: return JSON {"error": "Unknown tool: <name>"}
        - Handler raises: return JSON {"error": "Tool error: <message>"}
        - If the handler returns a non-string, json.dumps() it.
        """
        # TODO: implement routing with error handling
        pass


# ---------------------------------------------------------------------------
# Create registry and register tools — YOUR CODE HERE
# ---------------------------------------------------------------------------

registry = ToolRegistry()

# TODO: Register three tools using @registry.register(description):
#
#   scan_planet(planet_id: str) -> str
#       Look up planet_id in PLANET_DB.  Return the planet dict as JSON,
#       or {"error": "Unknown planet: <id>"} if not found.
#
#   check_habitability(atmosphere: str, gravity: float) -> str
#       Score habitability:
#         +50 for "nitrogen-oxygen" atmosphere, +20 for "nitrogen-argon"
#         +50 for gravity in [0.8, 1.2], +25 for gravity in [0.5, 1.5]
#       Return {"atmosphere": ..., "gravity": ..., "habitability_score": ...}
#
#   log_discovery(planet_id: str, summary: str) -> str
#       Append {"planet_id": ..., "summary": ...} to MISSION_LOG.
#       Return {"status": "logged", "entry": ...}


# ---------------------------------------------------------------------------
# Agent result + loop (provided — uses your registry)
# ---------------------------------------------------------------------------


@dataclass
class AgentResult:
    final_answer: str | None
    tool_calls_made: list[str] = field(default_factory=list)
    steps: int = 0


SYSTEM_PROMPT = (
    "You are the DSS Pathfinder exploration AI. Use your tools to scan planets, "
    "assess habitability, and log discoveries. Be concise."
)


def run_agent(client, question: str, max_steps: int = 5) -> AgentResult:
    """Agent loop that uses the ToolRegistry."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_calls_made: list[str] = []
    steps = 0

    for _ in range(max_steps):
        steps += 1
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=registry.list_tools(),
        )
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tc in message.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result = registry.execute(name, args)
                tool_calls_made.append(name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        elif message.content:
            return AgentResult(
                final_answer=message.content,
                tool_calls_made=tool_calls_made,
                steps=steps,
            )
        else:
            break

    return AgentResult(
        final_answer=None,
        tool_calls_made=tool_calls_made,
        steps=steps,
    )


# ---------------------------------------------------------------------------
# CLI chat loop
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI()
    print("DSS Pathfinder Exploration Agent (with auto-schema registry) ready. Type a question (or 'quit').\n")

    registered = registry.list_tools()
    if not registered:
        print("WARNING: No tools registered! Implement the ToolRegistry first.\n")
    else:
        print(f"Registered tools: {', '.join(t['function']['name'] for t in registered)}\n")

    while True:
        q = input("You: ").strip()
        if not q or q.lower() in ("quit", "exit"):
            break
        result = run_agent(client, q)
        print(f"\nAgent: {result.final_answer}")
        if result.tool_calls_made:
            print(f"  (tools used: {', '.join(result.tool_calls_made)})")
        print()
