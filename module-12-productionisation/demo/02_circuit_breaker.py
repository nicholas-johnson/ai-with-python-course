"""
Demo 02 — Circuit Breaker
===========================
Shows circuit breaker states: closed → open → half-open → closed.

Run:  python module-12-productionisation/demo/02_circuit_breaker.py
"""

import time
import random


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time: float = 5.0):
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_time = recovery_time
        self.last_failure_time = 0.0
        self.state = "closed"

    def call(self, fn):
        if self.state == "open":
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_time:
                self.state = "half-open"
                print(f"    [circuit] half-open — trying one test request (waited {elapsed:.1f}s)")
            else:
                raise CircuitOpenError(f"Circuit OPEN — failing fast ({self.recovery_time - elapsed:.1f}s until retry)")

        try:
            result = fn()
            if self.state == "half-open":
                print("    [circuit] test request succeeded — closing circuit")
            self.failures = 0
            self.state = "closed"
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
                print(f"    [circuit] OPENED — {self.failures} failures hit threshold")
            raise


def unreliable_service(fail_until: float):
    """Simulates a service that fails until a certain time, then recovers."""
    if time.time() < fail_until:
        raise ConnectionError("Service unavailable")
    return "Success!"


def demo_circuit_breaker():
    print("=" * 60)
    print("  DEMO: Circuit Breaker")
    print("=" * 60)

    breaker = CircuitBreaker(failure_threshold=3, recovery_time=4.0)
    fail_until = time.time() + 6.0

    for i in range(1, 16):
        time.sleep(0.8)
        print(f"\n  Request {i} (state: {breaker.state}):")
        try:
            result = breaker.call(lambda: unreliable_service(fail_until))
            print(f"    ✓ {result}")
        except CircuitOpenError as e:
            print(f"    ✗ {e}")
        except ConnectionError as e:
            print(f"    ✗ {e} (failure {breaker.failures}/{breaker.threshold})")

    print("\n  Done. The circuit protected the system during the outage.\n")


if __name__ == "__main__":
    demo_circuit_breaker()
