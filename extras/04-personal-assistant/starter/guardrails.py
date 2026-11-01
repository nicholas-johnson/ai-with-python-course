"""Safety guardrails — destructive action confirmation, PII redaction, token budget.

Techniques demonstrated:
- Confirmation prompts before destructive actions
- Regex-based PII redaction
- Session-level token budget tracking
"""

import re


def confirm_destructive_action(action_description: str) -> dict:
    """Return a confirmation prompt for destructive actions like deletes.

    Return: {"requires_confirmation": True, "message": "Are you sure..."}
    """
    # TODO: Return a confirmation dict
    pass


def redact_pii(text: str) -> str:
    """Redact emails, phone numbers, and national insurance numbers from text.

    Use regex to replace:
    - Email addresses → [EMAIL REDACTED]
    - Phone numbers (US/UK format) → [PHONE REDACTED]
    - NI numbers → [NI NUMBER REDACTED]
    """
    # TODO: Apply regex substitutions
    return text


class TokenBudget:
    """Track token usage and enforce a per-session budget."""

    def __init__(self, max_tokens: int = 50_000):
        self.max_tokens = max_tokens
        self.tokens_used = 0

    def record(self, tokens: int):
        """Record token usage."""
        # TODO: Increment tokens_used
        pass

    def check(self) -> bool:
        """Return True if within budget, False if exceeded."""
        # TODO: Compare tokens_used to max_tokens
        pass

    @property
    def remaining(self) -> int:
        # TODO: Return remaining tokens
        pass

    def summary(self) -> str:
        # TODO: Return a formatted summary string
        pass
