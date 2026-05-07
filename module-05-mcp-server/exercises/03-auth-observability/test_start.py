"""Tests for Exercise 03 — Auth + Observability."""

import pytest

from start import AuthContext, AuthenticatedToolRunner, ToolCallLog, check_scope


class TestAuthContext:
    def test_fields(self):
        ctx = AuthContext(user_id="CRW-001", role="captain", scopes={"crew:read", "mission:read"})
        assert ctx.user_id == "CRW-001"
        assert ctx.role == "captain"
        assert "crew:read" in ctx.scopes

    def test_default_scopes(self):
        ctx = AuthContext(user_id="CRW-099", role="ensign")
        assert ctx.scopes == set()


class TestCheckScope:
    def test_has_scope(self):
        ctx = AuthContext(user_id="u1", role="r", scopes={"crew:read", "logs:read"})
        assert check_scope(ctx, "crew:read") is True

    def test_missing_scope(self):
        ctx = AuthContext(user_id="u1", role="r", scopes={"crew:read"})
        assert check_scope(ctx, "mission:write") is False

    def test_empty_scopes(self):
        ctx = AuthContext(user_id="u1", role="r")
        assert check_scope(ctx, "anything") is False


class TestAuthenticatedToolRunner:
    @pytest.fixture()
    def runner(self):
        handlers = {
            "query_crew": lambda department="all": {"department": department, "count": 3},
            "launch_missile": lambda target="": {"launched": True, "target": target},
        }
        scopes = {
            "query_crew": "crew:read",
            "launch_missile": "weapons:fire",
        }
        return AuthenticatedToolRunner(handlers, scopes)

    def test_allowed_call(self, runner):
        auth = AuthContext(user_id="CRW-001", role="captain", scopes={"crew:read"})
        result = runner.call("query_crew", {"department": "science"}, auth)
        assert "result" in result
        assert result["result"]["count"] == 3

    def test_denied_call(self, runner):
        auth = AuthContext(user_id="CRW-005", role="ensign", scopes={"crew:read"})
        result = runner.call("launch_missile", {"target": "asteroid"}, auth)
        assert "error" in result
        assert "denied" in result["error"].lower()

    def test_unknown_tool(self, runner):
        auth = AuthContext(user_id="CRW-001", role="captain", scopes=set())
        result = runner.call("self_destruct", {}, auth)
        assert "error" in result
        assert "Unknown" in result["error"]

    def test_logging(self, runner):
        auth = AuthContext(user_id="CRW-001", role="captain", scopes={"crew:read"})
        runner.call("query_crew", {}, auth)

        assert len(runner.logs) == 1
        log = runner.logs[0]
        assert isinstance(log, ToolCallLog)
        assert log.user_id == "CRW-001"
        assert log.tool == "query_crew"
        assert log.allowed is True

    def test_denied_call_is_logged(self, runner):
        auth = AuthContext(user_id="CRW-005", role="ensign", scopes=set())
        runner.call("launch_missile", {}, auth)

        assert len(runner.logs) == 1
        assert runner.logs[0].allowed is False

    def test_multiple_calls_logged(self, runner):
        captain = AuthContext(user_id="CRW-001", role="captain", scopes={"crew:read", "weapons:fire"})
        runner.call("query_crew", {}, captain)
        runner.call("launch_missile", {"target": "debris"}, captain)
        assert len(runner.logs) == 2
