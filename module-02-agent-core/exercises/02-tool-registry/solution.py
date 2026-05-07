"""
Exercise 02 — Tool Registry (solution)
"""

import json
from dataclasses import dataclass
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
        missing = validate_required(tool.parameters, arguments)
        if missing:
            return json.dumps({"error": f"Missing required fields: {', '.join(missing)}"})

        try:
            result = tool.handler(**arguments)
            return json.dumps(result) if not isinstance(result, str) else result
        except Exception as exc:
            return json.dumps({"error": f"Tool error: {exc}"})


def validate_required(parameters_schema: dict, arguments: dict) -> list[str]:
    required = parameters_schema.get("required", [])
    return [f for f in required if f not in arguments]
