"""
Exercise 02 — Reliability

Three layers that keep a service answering while a dependency misbehaves:
retry with backoff and jitter, a circuit breaker, and a fallback chain.

No API key: the services in __main__ are simulated. Sleeping and the clock
are both injectable, so the tests assert the delay sequence and drive the
breaker through its states without waiting for real seconds to pass.
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
    """
    Call `fn`, retrying transient failures with a growing delay.

    Args:
        fn: Zero-argument callable. Raises TransientError or PermanentError.
        max_retries: Retries *after* the first attempt, so max_retries=3
            means up to four calls in total.
        base_delay: Seconds for the first delay; doubles each retry.
        sleep: Injected so tests can record delays instead of waiting.
        jitter: Returns a float in [0, 1). Injected so tests are deterministic.

    Returns:
        Whatever `fn` returns.

    Raises:
        PermanentError: immediately, without retrying.
        TransientError: after the final attempt fails.

    The delay before retry number `attempt` (0-based) is:

        base_delay * (2 ** attempt) + jitter() * base_delay

    With base_delay=1.0 and no jitter that is 1s, 2s, 4s. The jitter term
    spreads out clients that all failed during the same outage, so they do
    not return together and re-create the load that caused it.

    TODO:
    - Loop over attempt in range(max_retries + 1).
    - try: return fn()
    - except PermanentError: re-raise now. Retrying cannot help.
    - except TransientError: if this was the last attempt, re-raise.
      Otherwise compute the delay above, call sleep(delay), and continue.
    """
    # TODO: implement retry with backoff
    pass


# ---------------------------------------------------------------------------
# 2. Circuit breaker
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """
    Stops calling a dependency that is already failing.

    Three states:

        closed    — normal. Requests pass through.
        open      — tripped. Requests are rejected without being attempted,
                    so a dead dependency stops occupying connections.
        half-open — the cooldown has elapsed. Let a request through and see
                    what happens: success closes the circuit, failure opens
                    it again for another cooldown.

    Args:
        failure_threshold: Consecutive failures that trip the breaker.
        cooldown_seconds: How long to stay open before testing again.
        clock: Returns seconds as a float. The tests pass a fake.
    """

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
        """
        Decide whether a call may be attempted, moving open -> half-open
        once the cooldown has elapsed.

        TODO:
        - closed: return True.
        - open: if self._clock() - self.opened_at >= self.cooldown_seconds,
          set state to "half-open" and return True. Otherwise return False.
        - half-open: return True.
        """
        # TODO: implement the state check
        pass

    def record_success(self) -> None:
        """
        A call succeeded: the dependency is healthy again.

        TODO:
        - Reset failures to 0 and state to "closed".
        """
        # TODO: implement
        pass

    def record_failure(self) -> None:
        """
        A call failed: count it, and trip the breaker if we have hit the
        threshold. A failure while half-open re-opens the circuit, which
        falls out of the same check as long as you stamp opened_at.

        TODO:
        - Increment failures.
        - If failures >= failure_threshold (or state is "half-open"),
          set state to "open" and opened_at to self._clock().
        """
        # TODO: implement
        pass

    def call(self, fn: Callable[[], object]) -> object:
        """Run `fn` through the breaker. Provided — it wires up the three above."""
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
    """
    Try each rung of the chain in order and return the first answer.

    Args:
        chain: [(step_name, callable), ...] in order of preference —
            primary model, the same model with retries, a cheaper model,
            a cached response.

    Returns:
        {
            "answer": str,         # the answer, or FALLBACK_MESSAGE
            "step": str,           # which rung produced it, or "unavailable"
            "attempts": [          # the rungs that failed, in order
                {"step": str, "error": str},
            ],
        }

    Never raises. A chain that fails all the way down still returns a reply,
    because a degraded answer beats a stack trace in front of the crew.

    TODO:
    - Walk the chain. For each (name, fn):
        try: return {"answer": fn(), "step": name, "attempts": attempts}
        except Exception as exc: append {"step": name, "error": str(exc)}
    - If nothing worked, return FALLBACK_MESSAGE with step "unavailable".
    """
    # TODO: implement the fallback chain
    pass


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
        sleep=delays.append,  # record instead of waiting
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
