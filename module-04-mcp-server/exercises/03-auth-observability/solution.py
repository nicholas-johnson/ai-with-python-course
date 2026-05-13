"""
Exercise 03 — Auth + Observability (solution)
"""

import json
import time
from dataclasses import dataclass, field


@dataclass
class AuthContext:
    user_id: str
    role: str
    scopes: set[str] = field(default_factory=set)


def check_scope(context: AuthContext, required_scope: str) -> bool:
    return required_scope in context.scopes


@dataclass
class ToolCallLog:
    timestamp: float
    user_id: str
    tool: str
    arguments: dict
    allowed: bool
    result_preview: str


class AuthenticatedToolRunner:
    def __init__(
        self,
        tool_handlers: dict[str, callable],
        tool_scopes: dict[str, str],
    ):
        self._handlers = tool_handlers
        self._scopes = tool_scopes
        self.logs: list[ToolCallLog] = []

    def _log(self, user_id: str, tool: str, arguments: dict, allowed: bool, result_preview: str):
        self.logs.append(ToolCallLog(
            timestamp=time.time(),
            user_id=user_id,
            tool=tool,
            arguments=arguments,
            allowed=allowed,
            result_preview=result_preview[:200],
        ))

    def call(self, tool_name: str, arguments: dict, auth: AuthContext) -> dict:
        if tool_name not in self._handlers:
            self._log(auth.user_id, tool_name, arguments, False, "Unknown tool")
            return {"error": f"Unknown tool: {tool_name}"}

        required = self._scopes.get(tool_name, "")
        if required and not check_scope(auth, required):
            self._log(auth.user_id, tool_name, arguments, False, "Access denied")
            return {"error": f"Access denied: requires scope '{required}'"}

        try:
            result = self._handlers[tool_name](**arguments)
            result_str = json.dumps(result) if not isinstance(result, str) else result
            self._log(auth.user_id, tool_name, arguments, True, result_str)
            return {"result": result}
        except Exception as exc:
            self._log(auth.user_id, tool_name, arguments, True, f"Error: {exc}")
            return {"error": str(exc)}
