"""Exercise 04 — MCP Client (solution)"""

from __future__ import annotations

from typing import Any


class MCPClient:
    def __init__(self, tools: list[dict], call_fn) -> None:
        self._tools = {t["name"]: t for t in tools}
        self._call_fn = call_fn

    def discover_tools(self) -> dict[str, dict]:
        return {name: t["inputSchema"] for name, t in self._tools.items()}

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}

        schema = self._tools[name].get("inputSchema", {})
        required = schema.get("required", [])
        missing = [r for r in required if r not in arguments]
        if missing:
            return {"error": f"Missing required arguments: {', '.join(missing)}"}

        try:
            result = self._call_fn(name, arguments)
            return {"result": result}
        except Exception as exc:
            return {"error": f"Tool call failed: {exc}"}
