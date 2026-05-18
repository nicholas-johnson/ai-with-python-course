"""Tests for Exercise 03 — Guarded Agent."""

import json
import os
import time
from unittest.mock import MagicMock

import pytest

from start import (
    AgentResult,
    AllowList,
    AuditEntry,
    GuardedAgent,
    RateLimiter,
    registry,
)


# ---------------------------------------------------------------------------
# AllowList tests
# ---------------------------------------------------------------------------

class TestAllowList:
    def test_permitted_tool_allowed(self):
        al = AllowList(permitted={"ping", "status"})
        assert al.check("ping") is True

    def test_unpermitted_tool_blocked(self):
        al = AllowList(permitted={"ping"})
        assert al.check("delete_all") is False

    def test_empty_allowlist_blocks_everything(self):
        al = AllowList(permitted=set())
        assert al.check("anything") is False


# ---------------------------------------------------------------------------
# RateLimiter tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# GuardedAgent tests (mocked OpenAI client)
# ---------------------------------------------------------------------------

def _make_tool_call(tc_id, name, arguments):
    tc = MagicMock()
    tc.id = tc_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


def _make_response(content=None, tool_calls=None):
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message = msg
    return resp


class TestGuardedAgent:
    def _make_agent(self, client, permitted=None, max_calls=10):
        al = AllowList(permitted=permitted or {"scan_planet", "check_habitability"})
        rl = RateLimiter(max_calls=max_calls, window_seconds=60.0)
        return GuardedAgent(client, registry, al, rl)

    def test_allowed_tool_executes(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "scan_planet", {"planet_id": "TRAP-1e"}),
            ]),
            _make_response(content="TRAP-1e has a nitrogen-oxygen atmosphere."),
        ]
        agent = self._make_agent(client)
        result = agent.run("Scan TRAP-1e")

        assert result.final_answer == "TRAP-1e has a nitrogen-oxygen atmosphere."
        assert "scan_planet" in result.tool_calls_made
        assert len(result.audit_log) == 1
        assert result.audit_log[0].allowed is True

    def test_blocked_tool_returns_error_to_model(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "log_discovery", {"planet_id": "TRAP-1e", "summary": "test"}),
            ]),
            _make_response(content="I cannot log discoveries — that tool is restricted."),
        ]
        agent = self._make_agent(client, permitted={"scan_planet"})
        result = agent.run("Log a discovery about TRAP-1e")

        assert result.final_answer is not None
        assert len(result.audit_log) == 1
        assert result.audit_log[0].allowed is False
        assert "not permitted" in result.audit_log[0].result.lower()

        second_call_messages = client.chat.completions.create.call_args_list[1]
        messages = second_call_messages.kwargs.get("messages") or second_call_messages[1].get("messages", [])
        tool_msgs = [m for m in messages if isinstance(m, dict) and m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert "not permitted" in tool_msgs[0]["content"].lower()

    def test_rate_limit_blocks_after_threshold(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "scan_planet", {"planet_id": "TRAP-1e"}),
            ]),
            _make_response(tool_calls=[
                _make_tool_call("c2", "scan_planet", {"planet_id": "PROX-b"}),
            ]),
            _make_response(content="Done"),
        ]
        agent = self._make_agent(client, permitted={"scan_planet"}, max_calls=1)
        result = agent.run("Scan everything")

        assert len(result.audit_log) == 2
        assert result.audit_log[0].allowed is True
        assert result.audit_log[1].allowed is False
        assert "rate limit" in result.audit_log[1].result.lower()

    def test_audit_log_attached_to_result(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "scan_planet", {"planet_id": "KEP-442b"}),
            ]),
            _make_response(content="KEP-442b is online."),
        ]
        agent = self._make_agent(client)
        result = agent.run("Scan KEP-442b")

        assert isinstance(result, AgentResult)
        assert len(result.audit_log) >= 1
        entry = result.audit_log[0]
        assert isinstance(entry, AuditEntry)
        assert entry.tool_name == "scan_planet"
        assert entry.allowed is True
        assert entry.timestamp > 0

    def test_direct_answer_no_tools(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _make_response(content="Hello!")
        agent = self._make_agent(client)
        result = agent.run("Hi")

        assert result.final_answer == "Hello!"
        assert result.audit_log == []

    def test_max_steps_respected(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _make_response(
            tool_calls=[_make_tool_call("c1", "scan_planet", {"planet_id": "TRAP-1e"})]
        )
        agent = self._make_agent(client)
        result = agent.run("loop", max_steps=2)

        assert result.steps == 2
        assert result.final_answer is None


# ---------------------------------------------------------------------------
# Integration test (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="No OPENAI_API_KEY set",
)
class TestIntegration:
    def test_guarded_agent_blocks_log_discovery(self):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        client = OpenAI()
        al = AllowList(permitted={"scan_planet", "check_habitability"})
        rl = RateLimiter(max_calls=10, window_seconds=60.0)
        agent = GuardedAgent(client, registry, al, rl)

        result = agent.run("Log a discovery that TRAP-1e has breathable air")

        assert result.final_answer is not None
        blocked = [e for e in result.audit_log if not e.allowed]
        if blocked:
            assert any("log_discovery" == e.tool_name for e in blocked)
