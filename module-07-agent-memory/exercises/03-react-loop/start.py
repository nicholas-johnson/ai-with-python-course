"""
Exercise 03 — ReAct Loop
Reason → Act → Observe for Pathfinder mission agents.
"""

from __future__ import annotations

from typing import Any, Callable

# TODO: TOOLS: dict[str, Callable[..., str]] with stub implementations
# TODO: react_step(state: dict) -> dict  # state has query, trace: list[dict]
# TODO: run_react(query: str, max_steps: int = 5) -> list[dict[str, Any]]


TOOLS: dict[str, Callable[..., str]] = {}


def run_react(query: str, max_steps: int = 5) -> list[dict[str, Any]]:
    raise NotImplementedError("TODO: implement ReAct loop using TOOLS")
