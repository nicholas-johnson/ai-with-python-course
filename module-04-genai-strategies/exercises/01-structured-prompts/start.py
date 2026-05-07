"""
Exercise 01 — Structured Prompts
Build prompts that produce JSON-parseable mission status outputs.
"""

from __future__ import annotations

from typing import Any

# TODO: Define MISSION_STATUS_SCHEMA or a small dataclass / TypedDict
# TODO: build_prompt(user_message: str) -> str — returns full prompt for the model
# TODO: parse_mission_status(raw_model_text: str) -> dict[str, Any] — json.loads + validate


def build_prompt(user_message: str) -> str:
    raise NotImplementedError("TODO")


def parse_mission_status(raw_model_text: str) -> dict[str, Any]:
    raise NotImplementedError("TODO")
