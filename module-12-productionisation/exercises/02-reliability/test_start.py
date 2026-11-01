"""Tests for Exercise 02 — Reliability."""

import pytest
from start import (
    FALLBACK_MESSAGE,
    CircuitBreaker,
    CircuitOpenError,
    PermanentError,
    TransientError,
    chat_with_fallback,
    flaky_telemetry,
    retry_with_backoff,
)

NO_JITTER = (lambda: 0.0)


def counting(*outcomes):
    """A callable that yields the given outcomes in order; exceptions raise."""
    calls = {"n": 0}

    def fn():
        outcome = outcomes[min(calls["n"], len(outcomes) - 1)]
        calls["n"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    fn.calls = calls
    return fn


class TestRetryWithBackoff:
    def test_returns_immediately_on_success(self):
        delays = []
        fn = counting("hull integrity 98%")
        result = retry_with_backoff(fn, sleep=delays.append, jitter=NO_JITTER)
        assert result == "hull integrity 98%"
        assert fn.calls["n"] == 1
        assert delays == []

    def test_retries_transient_then_succeeds(self):
        delays = []
        fn = counting(TransientError("503"), TransientError("503"), "recovered")
        result = retry_with_backoff(fn, sleep=delays.append, jitter=NO_JITTER)
        assert result == "recovered"
        assert fn.calls["n"] == 3

    def test_delay_sequence_doubles(self):
        delays = []
        fn = counting(TransientError("503"))
        with pytest.raises(TransientError):
            retry_with_backoff(
                fn, max_retries=3, base_delay=1.0, sleep=delays.append, jitter=NO_JITTER
            )
        assert delays == [1.0, 2.0, 4.0]

    def test_base_delay_scales_the_sequence(self):
        delays = []
        fn = counting(TransientError("503"))
        with pytest.raises(TransientError):
            retry_with_backoff(
                fn, max_retries=2, base_delay=0.5, sleep=delays.append, jitter=NO_JITTER
            )
        assert delays == [0.5, 1.0]

    def test_jitter_is_added_on_top_of_the_delay(self):
        delays = []
        fn = counting(TransientError("503"))
        with pytest.raises(TransientError):
            retry_with_backoff(
                fn,
                max_retries=2,
                base_delay=1.0,
                sleep=delays.append,
                jitter=lambda: 0.5,
            )
        assert delays == [1.5, 2.5]

    def test_max_retries_means_attempts_plus_one(self):
        fn = counting(TransientError("503"))
        with pytest.raises(TransientError):
            retry_with_backoff(fn, max_retries=3, sleep=lambda _: None, jitter=NO_JITTER)
        assert fn.calls["n"] == 4  # first attempt + 3 retries

    def test_permanent_error_is_not_retried(self):
        delays = []
        fn = counting(PermanentError("401 unauthorised"))
        with pytest.raises(PermanentError):
            retry_with_backoff(fn, sleep=delays.append, jitter=NO_JITTER)
        assert fn.calls["n"] == 1
        assert delays == []

    def test_zero_retries_calls_once(self):
        fn = counting(TransientError("503"))
        with pytest.raises(TransientError):
            retry_with_backoff(fn, max_retries=0, sleep=lambda _: None, jitter=NO_JITTER)
        assert fn.calls["n"] == 1


class TestCircuitBreaker:
    def make(self, **kwargs):
        now = {"t": 0.0}
        kwargs.setdefault("failure_threshold", 3)
        kwargs.setdefault("cooldown_seconds", 30.0)
        breaker = CircuitBreaker(clock=lambda: now["t"], **kwargs)
        return breaker, now

    def test_starts_closed_and_allows_requests(self):
        breaker, _ = self.make()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_stays_closed_below_the_threshold(self):
        breaker, _ = self.make()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_opens_at_the_threshold(self):
        breaker, _ = self.make()
        for _ in range(3):
            breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.allow_request() is False

    def test_success_resets_the_failure_count(self):
        breaker, _ = self.make()
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.failures == 0
        breaker.record_failure()
        assert breaker.state == "closed"  # count restarted, not at 3

    def test_stays_open_during_cooldown(self):
        breaker, now = self.make()
        for _ in range(3):
            breaker.record_failure()
        now["t"] += 29.0
        assert breaker.allow_request() is False
        assert breaker.state == "open"

    def test_half_opens_once_cooldown_elapses(self):
        breaker, now = self.make()
        for _ in range(3):
            breaker.record_failure()
        now["t"] += 30.0
        assert breaker.allow_request() is True
        assert breaker.state == "half-open"

    def test_success_while_half_open_closes_the_circuit(self):
        breaker, now = self.make()
        for _ in range(3):
            breaker.record_failure()
        now["t"] += 31.0
        breaker.allow_request()
        breaker.record_success()
        assert breaker.state == "closed"
        assert breaker.failures == 0

    def test_failure_while_half_open_reopens_immediately(self):
        breaker, now = self.make()
        for _ in range(3):
            breaker.record_failure()
        now["t"] += 31.0
        breaker.allow_request()
        assert breaker.state == "half-open"

        breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.opened_at == now["t"]  # cooldown restarted
        assert breaker.allow_request() is False


class TestCircuitBreakerCall:
    def test_passes_through_when_closed(self):
        breaker = CircuitBreaker(failure_threshold=2, clock=lambda: 0.0)
        assert breaker.call(lambda: "nominal") == "nominal"

    def test_rejects_without_calling_once_open(self):
        now = {"t": 0.0}
        breaker = CircuitBreaker(
            failure_threshold=2, cooldown_seconds=10.0, clock=lambda: now["t"]
        )
        service = flaky_telemetry(fail_times=99)

        for _ in range(2):
            with pytest.raises(TransientError):
                breaker.call(service)
        assert breaker.state == "open"

        with pytest.raises(CircuitOpenError):
            breaker.call(service)

    def test_recovers_after_cooldown(self):
        now = {"t": 0.0}
        breaker = CircuitBreaker(
            failure_threshold=2, cooldown_seconds=10.0, clock=lambda: now["t"]
        )
        service = flaky_telemetry(fail_times=2)

        for _ in range(2):
            with pytest.raises(TransientError):
                breaker.call(service)
        assert breaker.state == "open"

        now["t"] += 11.0
        assert "Hull integrity" in breaker.call(service)
        assert breaker.state == "closed"


class TestChatWithFallback:
    def test_first_rung_wins(self):
        result = chat_with_fallback(
            [
                ("gpt-6-sol", lambda: "primary answer"),
                ("gpt-6-luna", lambda: "cheap answer"),
            ]
        )
        assert result["answer"] == "primary answer"
        assert result["step"] == "gpt-6-sol"
        assert result["attempts"] == []

    def test_falls_through_to_the_next_rung(self):
        def down():
            raise TransientError("gpt-6-sol unreachable")

        result = chat_with_fallback(
            [("gpt-6-sol", down), ("gpt-6-luna", lambda: "cheap answer")]
        )
        assert result["answer"] == "cheap answer"
        assert result["step"] == "gpt-6-luna"
        assert result["attempts"] == [
            {"step": "gpt-6-sol", "error": "gpt-6-sol unreachable"}
        ]

    def test_records_every_failed_rung_in_order(self):
        def down(name):
            def fn():
                raise TransientError(f"{name} unreachable")

            return fn

        result = chat_with_fallback(
            [
                ("gpt-6-sol", down("gpt-6-sol")),
                ("gpt-6-luna", down("gpt-6-luna")),
                ("cache", lambda: "cached answer"),
            ]
        )
        assert result["step"] == "cache"
        assert [a["step"] for a in result["attempts"]] == ["gpt-6-sol", "gpt-6-luna"]

    def test_returns_the_fallback_message_when_everything_fails(self):
        def down():
            raise TransientError("unreachable")

        result = chat_with_fallback([("gpt-6-sol", down), ("cache", down)])
        assert result["answer"] == FALLBACK_MESSAGE
        assert result["step"] == "unavailable"
        assert len(result["attempts"]) == 2

    def test_does_not_raise_even_on_an_unexpected_error(self):
        def boom():
            raise ValueError("something nobody planned for")

        result = chat_with_fallback([("gpt-6-sol", boom)])
        assert result["answer"] == FALLBACK_MESSAGE

    def test_empty_chain_returns_the_fallback_message(self):
        result = chat_with_fallback([])
        assert result["answer"] == FALLBACK_MESSAGE
        assert result["step"] == "unavailable"
        assert result["attempts"] == []
