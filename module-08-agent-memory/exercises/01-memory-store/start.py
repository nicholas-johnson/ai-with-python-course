"""
Exercise 01 — Memory Store
Short-term and long-term memory with decay for Pathfinder agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# TODO: SessionMemory — add_turn(role, content), get_context() -> list[dict]
# TODO: LongTermMemory — remember(key, value, do_not_remember=False), recall(prefix), tick_decay(factor=0.9)


@dataclass
class SessionMemory:
    turns: list[dict[str, str]] = field(default_factory=list)

    def add_turn(self, role: str, content: str) -> None:
        raise NotImplementedError("TODO")

    def get_context(self) -> list[dict[str, str]]:
        raise NotImplementedError("TODO")


@dataclass
class MemoryItem:
    key: str
    value: str
    score: float = 1.0
    forgotten: bool = False


@dataclass
class LongTermMemory:
    items: list[MemoryItem] = field(default_factory=list)

    def remember(self, key: str, value: str, do_not_remember: bool = False) -> None:
        raise NotImplementedError("TODO")

    def recall(self, prefix: str) -> list[MemoryItem]:
        raise NotImplementedError("TODO")

    def tick_decay(self, factor: float = 0.9) -> None:
        raise NotImplementedError("TODO")
