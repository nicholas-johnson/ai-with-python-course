"""
Exercise 03 — Auth + Observability
Per-tool auth scopes and structured logging.
"""

import time
from dataclasses import dataclass, field


@dataclass
class AuthContext:
    """Represents an authenticated user with scoped permissions."""

    # TODO: user_id (str), role (str), scopes (set[str])
    pass


def check_scope(context: AuthContext, required_scope: str) -> bool:
    """Return True if the context has the required scope."""
    # TODO: check if required_scope is in context.scopes
    pass


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
        """
        tool_handlers: {tool_name: callable}
        tool_scopes: {tool_name: required_scope_string}
        """
        self._handlers = tool_handlers
        self._scopes = tool_scopes
        self.logs: list[ToolCallLog] = []

    def call(self, tool_name: str, arguments: dict, auth: AuthContext) -> dict:
        """
        1. Check if tool_name exists. If not, return {"error": "Unknown tool"}.
        2. Check scope. If denied, log and return {"error": "Access denied"}.
        3. Call handler. Log the result. Return {"result": ...}.
        """
        # TODO: implement authenticated execution with logging
        pass
