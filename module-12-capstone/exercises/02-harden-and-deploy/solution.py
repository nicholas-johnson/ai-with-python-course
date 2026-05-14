"""
Exercise 02 — Harden and deploy (solution)
"""

from __future__ import annotations

import asyncio
import os
import random
import time
import uuid
from typing import Any

from fastapi import FastAPI


class TransientError(Exception):
    """Retriable failure — network blip, rate limit, or transient 5xx."""


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and calls are rejected."""


# ---------------------------------------------------------------------------
# 1. Structured tracing
# ---------------------------------------------------------------------------

class TraceContext:
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: list[dict] = []

    def start_span(self, name: str) -> dict:
        span = {
            "span_id": str(uuid.uuid4()),
            "trace_id": self.trace_id,
            "name": name,
            "start_time": time.time(),
        }
        self.spans.append(span)
        return span

    def end_span(self, span: dict, status: str = "ok", metadata: dict | None = None):
        span["end_time"] = time.time()
        span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
        span["status"] = status
        if metadata:
            span["metadata"] = metadata


# ---------------------------------------------------------------------------
# 2. Retry with exponential backoff
# ---------------------------------------------------------------------------

async def retry_with_backoff(
    fn,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Any:
    for attempt in range(max_retries):
        try:
            return await fn()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)


# ---------------------------------------------------------------------------
# 3. Circuit breaker
# ---------------------------------------------------------------------------

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_time: float = 60):
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_time = recovery_time
        self.last_failure_time = 0.0
        self.state = "closed"

    async def call(self, fn):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "half-open"
            else:
                raise CircuitOpenError("Service unavailable")

        try:
            result = await fn()
            self.failures = 0
            self.state = "closed"
            return result
        except Exception:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
            raise


# ---------------------------------------------------------------------------
# 4. Cost tracker
# ---------------------------------------------------------------------------

class CostTracker:
    def __init__(self, session_budget: int = 10_000, daily_budget: int = 1_000_000):
        self.session_usage = 0
        self.daily_usage = 0
        self.session_budget = session_budget
        self.daily_budget = daily_budget

    def record(self, prompt_tokens: int, completion_tokens: int):
        total = prompt_tokens + completion_tokens
        self.session_usage += total
        self.daily_usage += total

    def within_budget(self) -> bool:
        return (
            self.session_usage < self.session_budget
            and self.daily_usage < self.daily_budget
        )


# ---------------------------------------------------------------------------
# 5. Deployment — health-check app, config, Dockerfile validation
# ---------------------------------------------------------------------------

REQUIRED_DOCKERFILE_INSTRUCTIONS = ["FROM", "EXPOSE", "HEALTHCHECK", "CMD"]


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def load_config() -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    debug_raw = os.environ.get("DEBUG", "false").lower()

    return {
        "openai_api_key": api_key,
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "port": int(os.environ.get("PORT", "8000")),
        "debug": debug_raw in ("true", "1", "yes"),
    }


def validate_dockerfile(dockerfile_text: str) -> list[str]:
    upper = dockerfile_text.upper()
    return [instr for instr in REQUIRED_DOCKERFILE_INSTRUCTIONS if instr not in upper]
