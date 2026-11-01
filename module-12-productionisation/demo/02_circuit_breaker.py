"""
Demo 02 — Circuit Breaker
===========================
Shows the breaker moving through closed, open, half-open, and back to closed
while a ship service is unavailable.

No API key.

Run:  python module-12-productionisation/demo/02_circuit_breaker.py
"""

import time


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
            else:
                remaining = self.recovery_time - elapsed
                raise CircuitOpenError(f"circuit open, {remaining:.1f}s until the next attempt")

        try:
            result = fn()
            self.failures = 0
            self.state = "closed"
            return result
        except Exception:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
            raise


def telemetry_service(recovers_at: float):
    """A ship service that is down until `recovers_at`, then answers normally."""

    def service():
        if time.time() < recovers_at:
            raise ConnectionError("telemetry unavailable")
        return "hull integrity 98%, shields nominal"

    return service


def demo_circuit_breaker():
    print("=" * 60)
    print("  DEMO: Circuit Breaker")
    print("=" * 60)
    print("\n  Telemetry is down for the first 6 seconds. The breaker trips after")
    print("  3 failures and waits 4 seconds before testing the service again.\n")

    breaker = CircuitBreaker(failure_threshold=3, recovery_time=4.0)
    service = telemetry_service(recovers_at=time.time() + 6.0)

    for i in range(1, 16):
        time.sleep(0.8)
        before = breaker.state
        try:
            outcome = f"ok — {breaker.call(service)}"
        except CircuitOpenError as e:
            outcome = f"rejected — {e}"
        except ConnectionError as e:
            outcome = f"failed — {e} ({breaker.failures}/{breaker.threshold})"
        print(f"  {i:>2}  {before:<9} -> {breaker.state:<9}  {outcome}")

    print("\n  While the circuit was open, the service was never called —")
    print("  the requests were rejected locally in microseconds.\n")


if __name__ == "__main__":
    demo_circuit_breaker()
