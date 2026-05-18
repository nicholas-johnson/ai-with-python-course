"""
Exercise 02 — Tool Registry
Build a ToolRegistry class and wire it into the agent loop from Exercise 01.

The agent loop and ship data are provided (from Exercise 01's solution).
You only need to implement the ToolRegistry class and register the tools.
"""

import json
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Ship data (same as exercise 01)
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


# ---------------------------------------------------------------------------
# ToolRegistry — YOUR CODE HERE
# ---------------------------------------------------------------------------

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict):
        """
        Decorator that registers a function as a tool.

        Store the handler function alongside its schema so that:
        - list_tools() can build the OpenAI format
        - execute() can route calls to the right function

        Usage:
            @registry.register("tool_name", "description", {"type": "object", ...})
            def tool_name(arg: str) -> str:
                ...
        """
        # TODO: return a decorator that stores the tool and returns the function unchanged
        pass

    def list_tools(self) -> list[dict]:
        """
        Return tools in OpenAI-compatible format:
        [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
        """
        # TODO: build and return the tool list from self._tools
        pass

    def execute(self, name: str, arguments: dict) -> str:
        """
        Look up the tool by name and call its handler with the arguments.
        Return the result as a string.

        Error handling:
        - Unknown tool: return JSON {"error": "Unknown tool: <name>"}
        - Handler raises: return JSON {"error": "Tool error: <message>"}
        """
        # TODO: implement routing with error handling
        pass


# ---------------------------------------------------------------------------
# Create registry and register tools — YOUR CODE HERE
# ---------------------------------------------------------------------------

registry = ToolRegistry()

# TODO: use @registry.register(...) to register these three tools:
#   get_crew_count  — takes department, returns JSON with count
#   get_ship_status — takes system, returns JSON with status
#   search_crew     — takes query, returns JSON array of matches
#
# Example:
#   @registry.register("get_crew_count", "Get crew count for a department", {
#       "type": "object",
#       "properties": {"department": {"type": "string"}},
#       "required": ["department"],
#   })
#   def get_crew_count(department: str) -> str:
#       ...


# ---------------------------------------------------------------------------
# Agent result + loop (from Exercise 01 — already implemented)
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    final_answer: str | None
    tool_calls_made: list[str] = field(default_factory=list)
    steps: int = 0


SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Use your tools to answer crew and ship queries. Be concise."


def run_agent(client, question: str, max_steps: int = 5) -> AgentResult:
    """Agent loop that uses the ToolRegistry instead of raw dicts."""
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
    print("DSS Pathfinder Agent (with registry) ready. Type a question (or 'quit').\n")

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
