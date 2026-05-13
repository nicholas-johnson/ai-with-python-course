"""
Exercise 04 — MCP Client
Build a client that discovers, validates, and calls MCP tools.
"""

from __future__ import annotations

from typing import Any


class MCPClient:
    """Lightweight MCP client that wraps a server's tool interface.

    Parameters
    ----------
    tools : list[dict]
        A list of tool descriptors, each with "name", "description",
        and "inputSchema" (JSON Schema with "properties" and "required").
    call_fn : callable
        A function ``call_fn(tool_name, arguments) -> str`` that
        performs the actual tool call against the server.
    """

    def __init__(self, tools: list[dict], call_fn) -> None:
        raise NotImplementedError("TODO")

    def discover_tools(self) -> dict[str, dict]:
        """Return a dict mapping tool name → input schema."""
        raise NotImplementedError("TODO")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate arguments against the schema, then call the tool.

        Return ``{"result": <tool output>}`` on success.
        Return ``{"error": <message>}`` if the tool is unknown or
        required arguments are missing.
        """
        raise NotImplementedError("TODO")
