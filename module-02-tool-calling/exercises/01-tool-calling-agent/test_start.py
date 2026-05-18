"""Tests for Exercise 01 — Tool-Calling Agent."""

import json
import os
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from start import (
    TOOL_HANDLERS,
    TOOLS,
    AgentResult,
    run_agent,
)


# ---------------------------------------------------------------------------
# Tool schema validation
# ---------------------------------------------------------------------------

class TestToolSchemas:
    def test_tools_is_a_list(self):
        assert isinstance(TOOLS, list)
        assert len(TOOLS) == 3

    def test_each_tool_has_correct_structure(self):
        for tool in TOOLS:
            assert tool["type"] == "function"
            fn = tool["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
            assert fn["parameters"]["type"] == "object"

    def test_tool_names(self):
        names = {t["function"]["name"] for t in TOOLS}
        assert names == {"get_crew_count", "get_ship_status", "search_crew"}

    def test_required_fields_present(self):
        for tool in TOOLS:
            params = tool["function"]["parameters"]
            assert "required" in params
            assert len(params["required"]) > 0


# ---------------------------------------------------------------------------
# Tool handler tests
# ---------------------------------------------------------------------------

class TestToolHandlers:
    def test_all_tools_have_handlers(self):
        tool_names = {t["function"]["name"] for t in TOOLS}
        assert set(TOOL_HANDLERS.keys()) == tool_names

    def test_get_crew_count_known_department(self):
        result = json.loads(TOOL_HANDLERS["get_crew_count"](department="science"))
        assert result["department"] == "science"
        assert isinstance(result["count"], int)
        assert result["count"] > 0

    def test_get_crew_count_unknown_department(self):
        result = json.loads(TOOL_HANDLERS["get_crew_count"](department="nonexistent"))
        assert result["count"] == 0

    def test_get_ship_status_known_system(self):
        result = json.loads(TOOL_HANDLERS["get_ship_status"](system="warp"))
        assert result["system"] == "warp"
        assert "status" in result

    def test_get_ship_status_unknown_system(self):
        result = json.loads(TOOL_HANDLERS["get_ship_status"](system="cloaking"))
        assert result["status"] == "unknown"

    def test_search_crew_finds_match(self):
        results = json.loads(TOOL_HANDLERS["search_crew"](query="Voss"))
        assert len(results) >= 1
        assert any("Voss" in r["name"] for r in results)

    def test_search_crew_no_match(self):
        results = json.loads(TOOL_HANDLERS["search_crew"](query="zzzznotfound"))
        assert results == []


# ---------------------------------------------------------------------------
# Agent loop tests (mocked OpenAI client)
# ---------------------------------------------------------------------------

def _make_tool_call(tc_id, name, arguments):
    """Build a mock tool_call object matching the OpenAI SDK shape."""
    tc = MagicMock()
    tc.id = tc_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


def _make_response(content=None, tool_calls=None):
    """Build a mock chat completion response."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message = msg
    return resp


class TestRunAgent:
    def test_direct_answer_no_tools(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _make_response(
            content="Hello, Commander."
        )
        result = run_agent(client, "Hi")

        assert isinstance(result, AgentResult)
        assert result.final_answer == "Hello, Commander."
        assert result.tool_calls_made == []
        assert result.steps == 1

    def test_single_tool_call_then_answer(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "get_crew_count", {"department": "science"}),
            ]),
            _make_response(content="There are 3 in science."),
        ]
        result = run_agent(client, "How many in science?")

        assert result.final_answer == "There are 3 in science."
        assert result.tool_calls_made == ["get_crew_count"]
        assert result.steps == 2

    def test_multiple_tool_calls_across_steps(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "get_ship_status", {"system": "warp"}),
            ]),
            _make_response(tool_calls=[
                _make_tool_call("c2", "get_ship_status", {"system": "shields"}),
            ]),
            _make_response(content="Both systems online."),
        ]
        result = run_agent(client, "Status of warp and shields?")

        assert result.final_answer == "Both systems online."
        assert result.tool_calls_made == ["get_ship_status", "get_ship_status"]
        assert result.steps == 3

    def test_max_steps_prevents_infinite_loop(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _make_response(
            tool_calls=[_make_tool_call("c1", "get_crew_count", {"department": "science"})]
        )
        result = run_agent(client, "loop forever", max_steps=3)

        assert result.steps == 3
        assert result.final_answer is None

    def test_tool_results_passed_to_api(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _make_response(tool_calls=[
                _make_tool_call("c1", "get_crew_count", {"department": "science"}),
            ]),
            _make_response(content="Done"),
        ]
        run_agent(client, "test")

        second_call_messages = client.chat.completions.create.call_args_list[1]
        messages = second_call_messages.kwargs.get("messages") or second_call_messages[1].get("messages", [])
        tool_msgs = [m for m in messages if isinstance(m, dict) and m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert "science" in tool_msgs[0]["content"]


# ---------------------------------------------------------------------------
# Integration test (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="No OPENAI_API_KEY set",
)
class TestIntegration:
    def test_live_tool_call(self):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        client = OpenAI()
        result = run_agent(client, "How many crew are in the science department?")

        assert result.final_answer is not None
        assert "get_crew_count" in result.tool_calls_made
        assert result.steps >= 1
