"""
Exercise 10 — Advanced Guardrails

Chain content filtering, PII redaction, and schema validation
into a defensive pipeline for LLM inputs and outputs.
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

    Args:
        text: The text to check.
        blocked_patterns: List of regex patterns that are not allowed.

    Returns:
        Dict with:
        - "passed": bool (True if no patterns matched)
        - "reason": str or None (the matched pattern if blocked)

    TODO:
    - Check each pattern against the text (case-insensitive)
    - If any pattern matches, return passed=False with the pattern as reason
    - If no patterns match, return passed=True with reason=None
    """
    # TODO: implement content filtering
    pass


def redact_pii(text: str) -> str:
    """
    Find and redact PII (emails, phone numbers, SSNs) in text.

    Replaces each match with [REDACTED_TYPE] where TYPE is
    EMAIL, PHONE, or SSN.

    TODO:
    - Apply each pattern from PII_PATTERNS to the text
    - Replace matches with [REDACTED_{TYPE}] (uppercase)
    - Process SSN before PHONE to avoid partial matches
    - Return the redacted text
    """
    # TODO: implement PII redaction
    pass


def validate_output(data: dict) -> dict:
    """
    Validate a dict against the SafeResponse Pydantic model.

    Returns:
        Dict with:
        - "valid": bool
        - "data": the validated dict (if valid) or None
        - "errors": error string (if invalid) or None

    TODO:
    - Try to create a SafeResponse from the data
    - If valid, return the model_dump() as data
    - If invalid, catch ValidationError and return the error string
    """
    # TODO: implement schema validation
    pass


def guardrail_pipeline(
    text: str,
    blocked_patterns: list[str],
) -> dict:
    """
    Run the full guardrail pipeline: content check → PII redaction.

    Args:
        text: The input text to process.
        blocked_patterns: Patterns to block.

    Returns:
        Dict with:
        - "passed": bool
        - "reason": str or None (if blocked)
        - "cleaned_text": str (the text after PII redaction, if passed)

    TODO:
    - First check content against blocked patterns
    - If blocked, return immediately with passed=False
    - If passed, redact PII from the text
    - Return passed=True with the cleaned text
    """
    # TODO: implement guardrail pipeline
    pass
