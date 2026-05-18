"""
Exercise 02 — Tool Registry (solution)
"""

import json
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Ship data
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
# ToolRegistry
# ---------------------------------------------------------------------------

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict):
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "handler": fn,
            }
            return fn
        return decorator

    def list_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = self._tools[name]["handler"](**arguments)
            return result if isinstance(result, str) else json.dumps(result)
        except Exception as exc:
            return json.dumps({"error": f"Tool error: {exc}"})


# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------

registry = ToolRegistry()


@registry.register("get_crew_count", "Get the number of crew members in a department.", {
    "type": "object",
    "properties": {
        "department": {"type": "string", "description": "Department name (command, science, engineering, medical)"},
    },
    "required": ["department"],
})
def get_crew_count(department: str) -> str:
    crew = CREW_DATA.get(department, [])
    return json.dumps({"department": department, "count": len(crew)})


@registry.register("get_ship_status", "Get the current status of a ship system.", {
    "type": "object",
    "properties": {
        "system": {"type": "string", "description": "System name (warp, shields, sensors, life_support)"},
    },
    "required": ["system"],
})
def get_ship_status(system: str) -> str:
    status = SHIP_SYSTEMS.get(system, {"system": system, "status": "unknown"})
    return json.dumps(status)


@registry.register("search_crew", "Search crew members by name or role.", {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search term to match against crew names and roles"},
    },
    "required": ["query"],
})
def search_crew(query: str) -> str:
    matches = []
    q = query.lower()
    for dept, members in CREW_DATA.items():
        for member in members:
            if q in member["name"].lower() or q in member["role"].lower():
                matches.append({**member, "department": dept})
    return json.dumps(matches)


# ---------------------------------------------------------------------------
# Agent result + loop
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    final_answer: str | None
    tool_calls_made: list[str] = field(default_factory=list)
    steps: int = 0


SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Use your tools to answer crew and ship queries. Be concise."


def run_agent(client, question: str, max_steps: int = 5) -> AgentResult:
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
    print(f"Registered tools: {', '.join(t['function']['name'] for t in registry.list_tools())}\n")

    while True:
        q = input("You: ").strip()
        if not q or q.lower() in ("quit", "exit"):
            break
        result = run_agent(client, q)
        print(f"\nAgent: {result.final_answer}")
        if result.tool_calls_made:
            print(f"  (tools used: {', '.join(result.tool_calls_made)})")
        print()
