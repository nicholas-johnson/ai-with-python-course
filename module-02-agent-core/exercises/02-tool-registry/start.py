"""
Exercise 02 — Tool Registry
Build a tool registry with schema validation and routing.
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
        """
        Decorator that registers a function as a tool.
        Store a ToolSchema in self._tools.
        """
        # TODO: return a decorator that stores the tool and returns the function unchanged
        pass

    def list_tools(self) -> list[dict]:
        """
        Return tools in OpenAI-compatible format:
        [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
        """
        # TODO: build and return the tool list
        pass

    def call(self, name: str, arguments: dict) -> str:
        """
        Look up the tool by name, call its handler with arguments.
        Return the result as a JSON string.
        If tool not found, return {"error": "Unknown tool: <name>"}.
        If arguments invalid, return {"error": "Missing required fields: ..."}.
        If handler raises, return {"error": "Tool error: <message>"}.
        """
        # TODO: implement routing with error handling
        pass


def validate_required(parameters_schema: dict, arguments: dict) -> list[str]:
    """
    Check that all 'required' fields in the JSON schema are present in arguments.
    Return a list of missing field names (empty list if all present).
    """
    # TODO: extract required fields from schema, check against arguments keys
    pass
