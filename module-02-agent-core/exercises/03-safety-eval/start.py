"""
Exercise 03 — Safety Rails + Evaluation
Rate limiting, allowlists, and golden-file testing.
"""

import json
import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    max_calls: int
    window_seconds: float
    _timestamps: list[float] = field(default_factory=list)

    def allow(self) -> bool:
        """
        Return True if a new call is within the rate limit.
        Prune timestamps outside the window, then check count.
        If allowed, record the current timestamp.
        """
        # TODO: implement sliding-window rate limiting
        pass


@dataclass
class SafeToolResult:
    success: bool
    result: str


class SafeToolRunner:
    def __init__(
        self,
        tool_handlers: dict[str, callable],
        rate_limiter: RateLimiter,
        allowed_tools: set[str],
    ):
        self._handlers = tool_handlers
        self._rate_limiter = rate_limiter
        self._allowed = allowed_tools

    def call(self, name: str, arguments: dict) -> SafeToolResult:
        """
        1. Check if tool is in allowed_tools. If not, return error.
        2. Check rate_limiter.allow(). If not, return error.
        3. Call the handler. If it raises, return error.
        4. Return success result.
        """
        # TODO: implement guarded tool execution
        pass


@dataclass
class GoldenCase:
    name: str
    user_input: str
    expected_tool_names: list[str]
    expected_answer_contains: str | None = None


@dataclass
class GoldenResult:
    case_name: str
    passed: bool
    tool_names_match: bool
    answer_match: bool | None


def run_golden_test(
    case: GoldenCase,
    agent_fn: callable,
) -> GoldenResult:
    """
    Run agent_fn(case.user_input) and compare the result against expectations.
    agent_fn should return a dict with "tool_calls" (list of names) and "final_answer" (str).
    """
    # TODO: call agent_fn, compare tool names and answer
    pass
