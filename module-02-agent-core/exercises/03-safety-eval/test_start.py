"""Tests for Exercise 03 — Safety Rails + Evaluation."""

import json
import time

import pytest

from start import GoldenCase, GoldenResult, RateLimiter, SafeToolResult, SafeToolRunner, run_golden_test


class TestRateLimiter:
    def test_allows_within_limit(self):
        rl = RateLimiter(max_calls=3, window_seconds=10.0)
        assert rl.allow() is True
        assert rl.allow() is True
        assert rl.allow() is True

    def test_blocks_over_limit(self):
        rl = RateLimiter(max_calls=2, window_seconds=10.0)
        assert rl.allow() is True
        assert rl.allow() is True
        assert rl.allow() is False

    def test_window_expiry(self):
        rl = RateLimiter(max_calls=1, window_seconds=0.1)
        assert rl.allow() is True
        assert rl.allow() is False
        time.sleep(0.15)
        assert rl.allow() is True


class TestSafeToolRunner:
    @pytest.fixture()
    def runner(self):
        handlers = {
            "ping": lambda: {"status": "pong"},
            "secret": lambda: {"data": "classified"},
        }
        rl = RateLimiter(max_calls=5, window_seconds=60.0)
        return SafeToolRunner(handlers, rl, allowed_tools={"ping"})

    def test_allowed_tool_succeeds(self, runner):
        result = runner.call("ping", {})
        assert result.success is True
        assert "pong" in result.result

    def test_disallowed_tool_blocked(self, runner):
        result = runner.call("secret", {})
        assert result.success is False
        assert "not allowed" in result.result.lower()

    def test_unknown_tool_error(self, runner):
        result = runner.call("nonexistent", {})
        assert result.success is False

    def test_rate_limit_blocks(self):
        handlers = {"ping": lambda: {"status": "pong"}}
        rl = RateLimiter(max_calls=2, window_seconds=60.0)
        runner = SafeToolRunner(handlers, rl, allowed_tools={"ping"})

        runner.call("ping", {})
        runner.call("ping", {})
        result = runner.call("ping", {})
        assert result.success is False
        assert "rate limit" in result.result.lower()

    def test_handler_exception_caught(self):
        def explode():
            raise RuntimeError("warp core breach")

        handlers = {"boom": explode}
        rl = RateLimiter(max_calls=10, window_seconds=60.0)
        runner = SafeToolRunner(handlers, rl, allowed_tools={"boom"})

        result = runner.call("boom", {})
        assert result.success is False
        assert "warp core breach" in result.result


class TestGoldenTest:
    def test_passing_case(self):
        case = GoldenCase(
            name="simple query",
            user_input="How many in science?",
            expected_tool_names=["get_crew_count"],
            expected_answer_contains="3",
        )

        def fake_agent(user_input):
            return {"tool_calls": ["get_crew_count"], "final_answer": "There are 3 in science."}

        result = run_golden_test(case, fake_agent)
        assert isinstance(result, GoldenResult)
        assert result.passed is True
        assert result.tool_names_match is True
        assert result.answer_match is True

    def test_tool_names_mismatch(self):
        case = GoldenCase(
            name="wrong tools",
            user_input="test",
            expected_tool_names=["tool_a"],
        )

        def fake_agent(user_input):
            return {"tool_calls": ["tool_b"], "final_answer": "done"}

        result = run_golden_test(case, fake_agent)
        assert result.passed is False
        assert result.tool_names_match is False

    def test_answer_mismatch(self):
        case = GoldenCase(
            name="wrong answer",
            user_input="test",
            expected_tool_names=[],
            expected_answer_contains="hello",
        )

        def fake_agent(user_input):
            return {"tool_calls": [], "final_answer": "goodbye"}

        result = run_golden_test(case, fake_agent)
        assert result.passed is False
        assert result.answer_match is False

    def test_no_answer_check(self):
        case = GoldenCase(
            name="tools only",
            user_input="test",
            expected_tool_names=["a"],
        )

        def fake_agent(user_input):
            return {"tool_calls": ["a"], "final_answer": "anything"}

        result = run_golden_test(case, fake_agent)
        assert result.passed is True
        assert result.answer_match is None
