"""Tests for Exercise 02 — Harden and deploy."""

from __future__ import annotations

import asyncio
import os
import time

import pytest

from start import (
    CircuitBreaker,
    CircuitOpenError,
    CostTracker,
    TraceContext,
    TransientError,
    create_app,
    load_config,
    retry_with_backoff,
    validate_dockerfile,
)


# ---------------------------------------------------------------------------
# TraceContext
# ---------------------------------------------------------------------------

class TestTraceContext:
    def test_trace_id_is_unique(self):
        t1 = TraceContext()
        t2 = TraceContext()
        assert t1.trace_id != t2.trace_id

    def test_start_span_returns_span_dict(self):
        ctx = TraceContext()
        span = ctx.start_span("llm_call")
        assert span["name"] == "llm_call"
        assert span["trace_id"] == ctx.trace_id
        assert "span_id" in span
        assert "start_time" in span

    def test_end_span_records_duration(self):
        ctx = TraceContext()
        span = ctx.start_span("tool")
        time.sleep(0.01)
        ctx.end_span(span, status="ok", metadata={"tokens": 42})
        assert span["duration_ms"] >= 0
        assert span["status"] == "ok"
        assert span["metadata"]["tokens"] == 42

    def test_spans_accumulate(self):
        ctx = TraceContext()
        ctx.start_span("a")
        ctx.start_span("b")
        assert len(ctx.spans) == 2


# ---------------------------------------------------------------------------
# retry_with_backoff
# ---------------------------------------------------------------------------

class TestRetryWithBackoff:
    @pytest.mark.asyncio
    async def test_returns_on_first_success(self):
        async def ok():
            return "done"

        result = await retry_with_backoff(ok, max_retries=3, base_delay=0.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self):
        attempts = {"n": 0}

        async def flaky():
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise TransientError("busy")
            return "ok"

        result = await retry_with_backoff(flaky, max_retries=3, base_delay=0.0)
        assert result == "ok"
        assert attempts["n"] == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        async def always_fail():
            raise TransientError("nope")

        with pytest.raises(TransientError):
            await retry_with_backoff(always_fail, max_retries=2, base_delay=0.0)


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_passes_through_on_success(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_time=1)

        async def ok():
            return "result"

        assert await cb.call(ok) == "result"
        assert cb.state == "closed"

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_time=60)

        async def fail():
            raise ValueError("boom")

        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(fail)

        assert cb.state == "open"

    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_time=60)

        async def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await cb.call(fail)

        with pytest.raises(CircuitOpenError):
            await cb.call(fail)

    @pytest.mark.asyncio
    async def test_half_open_recovery(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_time=0)

        async def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await cb.call(fail)

        assert cb.state == "open"

        async def ok():
            return "recovered"

        await asyncio.sleep(0.01)
        result = await cb.call(ok)
        assert result == "recovered"
        assert cb.state == "closed"


# ---------------------------------------------------------------------------
# CostTracker
# ---------------------------------------------------------------------------

class TestCostTracker:
    def test_starts_within_budget(self):
        ct = CostTracker(session_budget=100, daily_budget=1000)
        assert ct.within_budget() is True

    def test_records_usage(self):
        ct = CostTracker(session_budget=100, daily_budget=1000)
        ct.record(prompt_tokens=30, completion_tokens=20)
        assert ct.session_usage == 50
        assert ct.daily_usage == 50

    def test_exceeds_session_budget(self):
        ct = CostTracker(session_budget=100, daily_budget=1000)
        ct.record(50, 60)
        assert ct.within_budget() is False

    def test_exceeds_daily_budget(self):
        ct = CostTracker(session_budget=10_000, daily_budget=100)
        ct.record(60, 50)
        assert ct.within_budget() is False


# ---------------------------------------------------------------------------
# Deployment helpers
# ---------------------------------------------------------------------------

class TestCreateApp:
    def test_health_endpoint_exists(self):
        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/health" in routes


class TestLoadConfig:
    def test_loads_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        config = load_config()
        assert config["openai_api_key"] == "sk-test-123"

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            load_config()

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        config = load_config()
        assert config["model"] == "gpt-4o-mini"

    def test_default_port(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("PORT", raising=False)
        config = load_config()
        assert config["port"] == 8000

    def test_debug_true(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("DEBUG", "true")
        config = load_config()
        assert config["debug"] is True

    def test_debug_false_by_default(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("DEBUG", raising=False)
        config = load_config()
        assert config["debug"] is False


class TestValidateDockerfile:
    def test_complete_dockerfile(self):
        dockerfile = (
            "FROM python:3.12-slim\n"
            "EXPOSE 8000\n"
            "HEALTHCHECK CMD curl localhost\n"
            'CMD ["uvicorn", "app:app"]\n'
        )
        assert validate_dockerfile(dockerfile) == []

    def test_missing_healthcheck(self):
        dockerfile = "FROM python:3.12\nEXPOSE 8000\nCMD uvicorn app:app\n"
        missing = validate_dockerfile(dockerfile)
        assert "HEALTHCHECK" in missing

    def test_empty_dockerfile(self):
        missing = validate_dockerfile("")
        assert len(missing) == 4
