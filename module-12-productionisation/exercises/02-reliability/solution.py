"""
Exercise 02 — Reliability (solution)

Retry with backoff and jitter, a circuit breaker, and a fallback chain.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable

FALLBACK_MESSAGE = (
    "I cannot reach the ship's systems right now. Please try again shortly."
)


class TransientError(Exception):
    """Worth retrying: 429, 500, 503, connection reset, read timeout."""


class PermanentError(Exception):
    """Not worth retrying: 400, 401, 404, a malformed request."""


class CircuitOpenError(Exception):
    """The breaker rejected the call without attempting it."""


# ---------------------------------------------------------------------------
# 1. Retry with exponential backoff and jitter
# ---------------------------------------------------------------------------


def retry_with_backoff(
    fn: Callable[[], object],
    max_retries: int = 3,
    base_delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    jitter: Callable[[], float] = random.random,
) -> object:
    """Call `fn`, retrying transient failures with a growing delay."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except PermanentError:
            raise  # retrying a 4xx just fails again, more slowly
        except TransientError:
            if attempt == max_retries:
                raise
            delay = base_delay * (2**attempt) + jitter() * base_delay
            sleep(delay)
    return None  # unreachable: the final attempt either returns or raises


# ---------------------------------------------------------------------------
# 2. Circuit breaker
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """Stops calling a dependency that is already failing."""

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.state = "closed"
        self.opened_at = 0.0
        self._clock = clock

    def allow_request(self) -> bool:
        if self.state == "open":
            if self._clock() - self.opened_at >= self.cooldown_seconds:
                self.state = "half-open"
                return True
            return False
        return True  # closed, or half-open and testing

    def record_success(self) -> None:
        self.failures = 0
        self.state = "closed"

    def record_failure(self) -> None:
        self.failures += 1
        if self.state == "half-open" or self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = self._clock()

    def call(self, fn: Callable[[], object]) -> object:
        """Run `fn` through the breaker."""
        if not self.allow_request():
            raise CircuitOpenError(f"Circuit open; not calling (failures={self.failures})")
        try:
            result = fn()
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result


# ---------------------------------------------------------------------------
# 3. Fallback chain
# ---------------------------------------------------------------------------


def chat_with_fallback(chain: list[tuple[str, Callable[[], str]]]) -> dict:
    """Try each rung of the chain in order and return the first answer."""
    attempts: list[dict] = []

    for name, fn in chain:
        try:
            return {"answer": fn(), "step": name, "attempts": attempts}
        except Exception as exc:
            attempts.append({"step": name, "error": str(exc)})

    return {"answer": FALLBACK_MESSAGE, "step": "unavailable", "attempts": attempts}


# ---------------------------------------------------------------------------
# Simulated ship services — provided.
# ---------------------------------------------------------------------------


def flaky_telemetry(fail_times: int) -> Callable[[], str]:
    """A service that raises TransientError the first `fail_times` calls."""
    calls = {"n": 0}

    def service() -> str:
        calls["n"] += 1
        if calls["n"] <= fail_times:
            raise TransientError(f"503 from telemetry (call {calls['n']})")
        return f"Hull integrity 98%, shields nominal (call {calls['n']})"

    return service


def always_down(name: str) -> Callable[[], str]:
    """A service that is simply unavailable."""

    def service() -> str:
        raise TransientError(f"{name} unreachable")

    return service


if __name__ == "__main__":
    print("1. Retry with backoff — telemetry fails twice, then recovers\n")
    delays: list[float] = []
    result = retry_with_backoff(
        flaky_telemetry(fail_times=2),
        base_delay=0.5,
        sleep=delays.append,
        jitter=lambda: 0.0,
    )
    print(f"   delays: {delays}")
    print(f"   result: {result}\n")

    print("2. Circuit breaker — three failures trip it, then it recovers\n")
    now = {"t": 0.0}
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=10.0, clock=lambda: now["t"])
    service = flaky_telemetry(fail_times=4)
    for _ in range(7):
        now["t"] += 4.0
        before = breaker.state
        try:
            outcome = f"ok — {breaker.call(service)}"
        except CircuitOpenError as exc:
            outcome = f"rejected — {exc}"
        except TransientError as exc:
            outcome = f"failed — {exc}"
        print(f"   t={now['t']:>4.0f}s  {before:<9} -> {breaker.state:<9}  {outcome}")

    print("\n3. Fallback chain — every rung is down, the crew still gets a reply\n")
    outcome = chat_with_fallback(
        [
            ("gpt-6-sol", always_down("gpt-6-sol")),
            ("gpt-6-luna", always_down("gpt-6-luna")),
            ("cache", always_down("cache")),
        ]
    )
    print(f"   {outcome}")
