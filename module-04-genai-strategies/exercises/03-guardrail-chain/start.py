"""
Exercise 03 — Guardrail Chain
Schema validation, content filter, and confidence threshold.
"""

from __future__ import annotations

from typing import Any

# TODO: validate_schema(payload: dict[str, Any]) -> tuple[bool, str]
# TODO: content_filter(text: str) -> tuple[bool, str]  # e.g. block classified keywords
# TODO: run_guardrails(raw: dict[str, Any], min_confidence: float) -> dict[str, Any]
# Return e.g. {"ok": bool, "errors": list[str]}


def validate_schema(payload: dict[str, Any]) -> tuple[bool, str]:
    raise NotImplementedError("TODO")


def content_filter(text: str) -> tuple[bool, str]:
    raise NotImplementedError("TODO")


def run_guardrails(raw: dict[str, Any], min_confidence: float) -> dict[str, Any]:
    raise NotImplementedError("TODO")
