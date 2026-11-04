"""Safety guardrails — destructive action confirmation, PII redaction, token budget."""

import re


def confirm_destructive_action(action_description: str) -> dict:
    """Return a confirmation prompt for destructive actions like deletes."""
    return {
        "requires_confirmation": True,
        "message": f"Are you sure you want to: {action_description}? Reply 'yes' to confirm.",
    }


def redact_pii(text: str) -> str:
    """Redact emails, phone numbers, and national insurance numbers from text."""
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL REDACTED]", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE REDACTED]", text)
    text = re.sub(r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b", "[NI NUMBER REDACTED]", text)
    return text


class TokenBudget:
    """Track token usage and enforce a per-session budget."""

    def __init__(self, max_tokens: int = 50_000):
        self.max_tokens = max_tokens
        self.tokens_used = 0

    def record(self, tokens: int):
        self.tokens_used += tokens

    def check(self) -> bool:
        """Return True if within budget, False if exceeded."""
        return self.tokens_used < self.max_tokens

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    def summary(self) -> str:
        pct = round(self.tokens_used / self.max_tokens * 100, 1)
        return f"Tokens: {self.tokens_used:,}/{self.max_tokens:,} ({pct}% used)"
