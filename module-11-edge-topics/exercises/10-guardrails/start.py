"""
Exercise 10 — Advanced Guardrails (Solution)

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
    """
    for pattern in blocked_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"passed": False, "reason": f"Matched blocked pattern: {pattern}"}
    return {"passed": True, "reason": None}


def redact_pii(text: str) -> str:
    """
    Find and redact PII in text.
    """
    for pii_type in ["ssn", "email", "phone"]:
        pattern = PII_PATTERNS[pii_type]
        text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text


def validate_output(data: dict) -> dict:
    """
    Validate a dict against the SafeResponse Pydantic model.
    """
    try:
        validated = SafeResponse(**data)
        return {"valid": True, "data": validated.model_dump(), "errors": None}
    except ValidationError as e:
        return {"valid": False, "data": None, "errors": str(e)}


def guardrail_pipeline(
    text: str,
    blocked_patterns: list[str],
) -> dict:
    """
    Run the full guardrail pipeline: content check → PII redaction.
    """
    content_check = check_content(text, blocked_patterns)
    if not content_check["passed"]:
        return {
            "passed": False,
            "reason": content_check["reason"],
            "cleaned_text": None,
        }

    cleaned = redact_pii(text)
    return {
        "passed": True,
        "reason": None,
        "cleaned_text": cleaned,
    }
