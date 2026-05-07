"""
Exercise 02 — Conversation Summary
Summarise long conversations to fit a context window.
"""

from __future__ import annotations

from typing import Any

# TODO: trim_turns(turns: list[dict[str, str]], max_tokens: int) -> list[dict[str, str]]
# TODO: summarise_turns(turns, max_tokens) -> str  # may call a stub "model" or heuristic


def trim_turns(turns: list[dict[str, str]], max_tokens: int) -> list[dict[str, str]]:
    raise NotImplementedError("TODO")


def summarise_turns(turns: list[dict[str, str]], max_tokens: int) -> str:
    raise NotImplementedError("TODO")
