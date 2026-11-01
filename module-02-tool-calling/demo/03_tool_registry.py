"""Part 3: Tool registry — decorator-registered tools, live agent."""

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def agent_loop(client: OpenAI, messages: list[dict], tools_list: list[dict], tool_handler):
    """One turn: call the model, run any tool calls, print the answer."""
    response = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages, tools=tools_list
    )
    calls = [item for item in response.output if item.type == "function_call"]

    if not calls:
        messages.append({"role": "assistant", "content": response.output_text})
        print(f"  [ASSISTANT] {response.output_text}\n")
        return

    messages += response.output
    for tc in calls:
        args = json.loads(tc.arguments)
        print(f"  [FUNCTION_CALL] {tc.name}({tc.arguments})")
        result, allowed = tool_handler(tc.name, args)
        tag = "ALLOWED" if allowed else "BLOCKED"
        print(f"  [{tag}]     {tc.name} → {result[:120]}")
        messages.append({"type": "function_call_output", "call_id": tc.call_id, "output": result})

    final = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages, tools=tools_list
    )
    answer = final.output_text
    messages.append({"role": "assistant", "content": answer})
    print(f"  [ASSISTANT] {answer}\n")


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSchema] = {}

    def register(self, name: str, description: str, parameters: dict):
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = ToolSchema(
                name=name, description=description, parameters=parameters, handler=fn
            )
            return fn
        return decorator

    def list_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})
        tool = self._tools[name]
        try:
            result = tool.handler(**arguments)
            return json.dumps(result) if not isinstance(result, str) else result
        except TypeError as exc:
            return json.dumps({"error": f"Invalid arguments: {exc}"})
        except Exception as exc:
            return json.dumps({"error": f"Tool error: {exc}"})


registry = ToolRegistry()


@registry.register(
    name="get_crew_count",
    description="Returns the number of crew members in a department.",
    parameters={
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Department name"},
        },
        "required": ["department"],
    },
)
def get_crew_count(department: str) -> dict:
    counts = {"command": 1, "science": 3, "engineering": 2, "operations": 3}
    return {"department": department, "count": counts.get(department, 0)}


@registry.register(
    name="ship_status",
    description="Returns current status of a ship system.",
    parameters={
        "type": "object",
        "properties": {
            "system": {"type": "string", "description": "System name"},
        },
        "required": ["system"],
    },
)
def ship_status(system: str) -> dict:
    systems = {
        "warp": {"system": "warp", "status": "online", "efficiency": 0.97},
        "shields": {"system": "shields", "status": "online", "efficiency": 0.85},
        "sensors": {"system": "sensors", "status": "degraded", "efficiency": 0.62},
    }
    return systems.get(system, {"system": system, "status": "unknown"})


def demo_tool_registry(client: OpenAI):
    print("=" * 60)
    print("PART 3: TOOL REGISTRY")
    print("=" * 60)
    print()

    print("  Registered tools (via @registry.register decorator):")
    for tool in registry.list_tools():
        params = ", ".join(tool["parameters"].get("required", []))
        print(f"    • {tool['name']}({params}) — {tool['description']}")

    print("\n  Chat with the agent. The LLM picks which tool to call;")
    print("  the registry dispatches to the right handler.")
    print("  Type 'quit' to return to the menu.\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. Use get_crew_count to look up "
                "department headcounts and ship_status to check system health. "
                "Always report exact numbers from the tools."
            ),
        },
    ]

    def handle_via_registry(name: str, arguments: dict) -> tuple[str, bool]:
        result = registry.call(name, arguments)
        return result, True

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        print(f"  [USER]      {user_msg}")
        agent_loop(client, messages, registry.list_tools(), handle_via_registry)

    print("  Key concepts:")
    print("  • @registry.register() decorator — schema lives next to the handler")
    print("  • list_tools() returns OpenAI-compatible function definitions")
    print("  • call() dispatches by name with argument validation")
    print("  • Unknown tools and bad arguments return errors, not crashes")
