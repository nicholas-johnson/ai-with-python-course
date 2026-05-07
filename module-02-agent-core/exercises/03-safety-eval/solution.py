"""
Exercise 03 — Safety Rails + Evaluation (solution)
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
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < self.window_seconds]
        if len(self._timestamps) >= self.max_calls:
            return False
        self._timestamps.append(now)
        return True


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
        if name not in self._allowed:
            return SafeToolResult(success=False, result=json.dumps({"error": f"Tool not allowed: {name}"}))

        if not self._rate_limiter.allow():
            return SafeToolResult(success=False, result=json.dumps({"error": "Rate limit exceeded"}))

        if name not in self._handlers:
            return SafeToolResult(success=False, result=json.dumps({"error": f"Unknown tool: {name}"}))

        try:
            result = self._handlers[name](**arguments)
            result_str = json.dumps(result) if not isinstance(result, str) else result
            return SafeToolResult(success=True, result=result_str)
        except Exception as exc:
            return SafeToolResult(success=False, result=json.dumps({"error": f"Tool error: {exc}"}))


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
    result = agent_fn(case.user_input)
    actual_tool_names = result.get("tool_calls", [])
    tool_names_match = actual_tool_names == case.expected_tool_names

    answer_match = None
    if case.expected_answer_contains is not None:
        final = result.get("final_answer", "") or ""
        answer_match = case.expected_answer_contains.lower() in final.lower()

    passed = tool_names_match and (answer_match is None or answer_match)
    return GoldenResult(
        case_name=case.name,
        passed=passed,
        tool_names_match=tool_names_match,
        answer_match=answer_match,
    )
