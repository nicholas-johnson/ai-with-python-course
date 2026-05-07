"""
Exercise 02 — Batch Pipeline
Batch LLM requests with retry and fallback.
"""

from __future__ import annotations


class TransientError(Exception):
    """Simulated rate limit / timeout — should trigger retry."""


def complete_batch(
    prompts: list[str],
    primary_fn,
    fallback_fn,
    max_retries: int = 2,
) -> list[str]:
    raise NotImplementedError("TODO")
