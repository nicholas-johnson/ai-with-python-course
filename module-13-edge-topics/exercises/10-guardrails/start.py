"""
Exercise 10 — Advanced Guardrails

Chain content filtering, PII redaction, and schema validation
into a defensive pipeline for LLM inputs and outputs.

TODO: Implement each function below.
"""

import re
from pydantic import BaseModel, ValidationError


class SafeResponse(BaseModel):
    """Expected output schema for validated responses."""
    answer: str
    confidence: float
    sources: list[str]


PII_PATTERNS = {
    "email": r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
}


def check_content(text: str, blocked_patterns: list[str]) -> dict:
    """
    Check text against blocked regex patterns.
    Returns {"passed": bool, "reason": str | None}.
    """
    raise NotImplementedError


def redact_pii(text: str) -> str:
    """
    Find and redact PII in text using PII_PATTERNS.
    Replace matches with [REDACTED_TYPE] tokens.
    """
    raise NotImplementedError


def validate_output(data: dict) -> dict:
    """
    Validate a dict against the SafeResponse Pydantic model.
    Returns {"valid": bool, "data": dict | None, "errors": str | None}.
    """
    raise NotImplementedError


def guardrail_pipeline(
    text: str,
    blocked_patterns: list[str],
) -> dict:
    """
    Run the full guardrail pipeline: content check -> PII redaction.
    Returns {"passed": bool, "reason": str | None, "cleaned_text": str | None}.
    """
    raise NotImplementedError
