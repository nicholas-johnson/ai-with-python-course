"""
Exercise 02 — Auto-Schema Tool Registry (solution)

A ToolRegistry that auto-generates OpenAI-compatible JSON schemas from Python
type hints, wired into an agent that explores exoplanets.
"""

import inspect
import json
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Type mapping: Python types → JSON Schema types
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
# ToolRegistry — auto-schema from type hints
# ---------------------------------------------------------------------------


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, description: str):
        """Decorator that registers a function as a tool.

        The function's name becomes the tool name.  The JSON schema is built
        automatically from inspect.signature() and the parameter annotations.
        """
        def decorator(fn: Callable) -> Callable:
            sig = inspect.signature(fn)
            properties: dict[str, dict] = {}
            required: list[str] = []

            for param_name, param in sig.parameters.items():
                json_type = TYPE_MAP.get(param.annotation, "string")
                properties[param_name] = {"type": json_type}
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            self._tools[fn.__name__] = {
                "name": fn.__name__,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
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
# Create registry and register planetary tools
# ---------------------------------------------------------------------------

registry = ToolRegistry()


@registry.register("Scan a planet by its catalog ID and return its data.")
def scan_planet(planet_id: str) -> str:
    planet = PLANET_DB.get(planet_id)
    if planet is None:
        return json.dumps({"error": f"Unknown planet: {planet_id}"})
    return json.dumps(planet)


@registry.register("Check habitability given an atmosphere type and surface gravity.")
def check_habitability(atmosphere: str, gravity: float) -> str:
    score = 0.0
    if atmosphere == "nitrogen-oxygen":
        score += 50.0
    elif atmosphere == "nitrogen-argon":
        score += 20.0
    if 0.8 <= gravity <= 1.2:
        score += 50.0
    elif 0.5 <= gravity <= 1.5:
        score += 25.0
    return json.dumps({"atmosphere": atmosphere, "gravity": gravity, "habitability_score": score})


@registry.register("Log a discovery to the mission log.")
def log_discovery(planet_id: str, summary: str) -> str:
    entry = {"planet_id": planet_id, "summary": summary}
    MISSION_LOG.append(entry)
    return json.dumps({"status": "logged", "entry": entry})


# ---------------------------------------------------------------------------
# Agent result + loop
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
