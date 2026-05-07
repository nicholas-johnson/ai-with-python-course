"""Tests for Exercise 01 — Tool Loop."""

import json

import pytest

from start import LLMResponse, LoopResult, ToolCall, run_tool_loop


class FakeLLM:
    """Returns pre-scripted responses in sequence."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self._index = 0

    def chat(self, messages: list[dict]) -> LLMResponse:
        if self._index >= len(self._responses):
            return LLMResponse(content="(exhausted)")
        resp = self._responses[self._index]
        self._index += 1
        return resp


def echo_tool(**kwargs) -> str:
    return json.dumps(kwargs)


class TestToolLoopBasics:
    def test_direct_answer_no_tools(self):
        llm = FakeLLM([LLMResponse(content="Hello, Commander.")])
        result = run_tool_loop(llm, {}, "Hi")

        assert isinstance(result, LoopResult)
        assert result.final_answer == "Hello, Commander."
        assert result.tool_calls_made == []
        assert result.steps == 1

    def test_single_tool_call_then_answer(self):
        llm = FakeLLM([
            LLMResponse(tool_calls=[
                ToolCall(id="c1", name="echo", arguments={"msg": "ping"}),
            ]),
            LLMResponse(content="Tool said: ping"),
        ])
        result = run_tool_loop(llm, {"echo": echo_tool}, "test")

        assert result.final_answer == "Tool said: ping"
        assert len(result.tool_calls_made) == 1
        assert result.tool_calls_made[0].name == "echo"
        assert result.steps == 2

    def test_multiple_tool_calls(self):
        llm = FakeLLM([
            LLMResponse(tool_calls=[
                ToolCall(id="c1", name="echo", arguments={"a": "1"}),
            ]),
            LLMResponse(tool_calls=[
                ToolCall(id="c2", name="echo", arguments={"a": "2"}),
            ]),
            LLMResponse(content="Done"),
        ])
        result = run_tool_loop(llm, {"echo": echo_tool}, "test")

        assert result.final_answer == "Done"
        assert len(result.tool_calls_made) == 2
        assert result.steps == 3


class TestToolLoopEdgeCases:
    def test_max_steps_prevents_infinite_loop(self):
        infinite_tool_calls = [
            LLMResponse(tool_calls=[ToolCall(id=f"c{i}", name="echo", arguments={})])
            for i in range(20)
        ]
        llm = FakeLLM(infinite_tool_calls)
        result = run_tool_loop(llm, {"echo": echo_tool}, "test", max_steps=3)

        assert result.steps == 3
        assert result.final_answer is None

    def test_tool_results_passed_back(self):
        messages_seen = []

        class SpyLLM:
            def __init__(self):
                self._call = 0

            def chat(self, messages):
                messages_seen.append(list(messages))
                self._call += 1
                if self._call == 1:
                    return LLMResponse(tool_calls=[
                        ToolCall(id="c1", name="echo", arguments={"data": "sensor"}),
                    ])
                return LLMResponse(content="Got it")

        run_tool_loop(SpyLLM(), {"echo": echo_tool}, "read sensor")

        last_call_messages = messages_seen[-1]
        tool_msgs = [m for m in last_call_messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        assert "sensor" in tool_msgs[0]["content"]
