"""
Demo: Tool registry pattern — register, validate, route, handle errors.
Run:  python module-02-agent-core/demo/02_tool_registry.py
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable


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
        """Decorator to register a tool handler with its schema."""
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = ToolSchema(
                name=name,
                description=description,
                parameters=parameters,
                handler=fn,
            )
            return fn
        return decorator

    def list_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
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
    counts = {"command": 1, "science": 3, "engineering": 2, "operations": 3, "medical": 1, "security": 1}
    count = counts.get(department, 0)
    return {"department": department, "count": count}


@registry.register(
    name="ship_status",
    description="Returns current status of a ship system.",
    parameters={
        "type": "object",
        "properties": {
            "system": {"type": "string", "description": "System name (warp, shields, sensors)"},
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


if __name__ == "__main__":
    print("=== Tool Registry Demo ===\n")

    print("Registered tools:")
    for tool in registry.list_tools():
        fn = tool["function"]
        print(f"  {fn['name']}: {fn['description']}")

    print("\n--- Calling tools ---\n")

    result = registry.call("get_crew_count", {"department": "science"})
    print(f"get_crew_count(science) -> {result}")

    result = registry.call("ship_status", {"system": "sensors"})
    print(f"ship_status(sensors)    -> {result}")

    result = registry.call("unknown_tool", {})
    print(f"unknown_tool()          -> {result}")

    result = registry.call("get_crew_count", {"wrong_param": "x"})
    print(f"get_crew_count(bad)     -> {result}")
