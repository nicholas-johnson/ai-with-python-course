"""Tests for Exercise 04 — Agentic RAG."""

import json
from unittest.mock import MagicMock
from start import SEARCH_TOOL, handle_tool_call, agentic_rag


class TestSearchToolDefinition:
    def test_has_type_function(self):
        assert SEARCH_TOOL.get("type") == "function"

    def test_has_function_name(self):
        assert SEARCH_TOOL.get("function", {}).get("name") == "search_documents"

    def test_has_query_parameter(self):
        params = SEARCH_TOOL.get("function", {}).get("parameters", {})
        props = params.get("properties", {})
        assert "query" in props
        assert props["query"].get("type") == "string"

    def test_query_is_required(self):
        params = SEARCH_TOOL.get("function", {}).get("parameters", {})
        assert "query" in params.get("required", [])


class TestHandleToolCall:
    def test_calls_search_fn(self):
        tool_call = MagicMock()
        tool_call.function.name = "search_documents"
        tool_call.function.arguments = json.dumps({"query": "reactor temp"})

        search_fn = MagicMock(return_value=[{"text": "Result 1"}])
        result = handle_tool_call(tool_call, search_fn)

        search_fn.assert_called_once_with("reactor temp")
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_returns_json_string(self):
        tool_call = MagicMock()
        tool_call.function.name = "search_documents"
        tool_call.function.arguments = json.dumps({"query": "test"})

        search_fn = MagicMock(return_value=["result"])
        result = handle_tool_call(tool_call, search_fn)
        assert isinstance(result, str)
        json.loads(result)


class TestAgenticRag:
    def test_returns_answer_when_no_tool_calls(self):
        client = MagicMock()
        response = MagicMock()
        message = MagicMock()
        message.tool_calls = None
        message.content = "The answer is 42."
        response.choices = [MagicMock()]
        response.choices[0].message = message
        client.chat.completions.create.return_value = response

        result = agentic_rag(client, "What is the answer?", lambda q: [])
        assert result == "The answer is 42."

    def test_handles_tool_call_then_answers(self):
        client = MagicMock()

        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.function.name = "search_documents"
        tool_call.function.arguments = json.dumps({"query": "reactor"})

        tool_response = MagicMock()
        tool_message = MagicMock()
        tool_message.tool_calls = [tool_call]
        tool_message.content = None
        tool_response.choices = [MagicMock()]
        tool_response.choices[0].message = tool_message

        final_response = MagicMock()
        final_message = MagicMock()
        final_message.tool_calls = None
        final_message.content = "Based on the search, the reactor is stable."
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = final_message

        client.chat.completions.create.side_effect = [tool_response, final_response]

        search_fn = MagicMock(return_value=[{"text": "Reactor status: stable"}])
        result = agentic_rag(client, "How is the reactor?", search_fn)
        assert "reactor" in result.lower()
        search_fn.assert_called_once()

    def test_respects_max_turns(self):
        client = MagicMock()

        tool_call = MagicMock()
        tool_call.id = "call_loop"
        tool_call.function.name = "search_documents"
        tool_call.function.arguments = json.dumps({"query": "infinite"})

        loop_response = MagicMock()
        loop_message = MagicMock()
        loop_message.tool_calls = [tool_call]
        loop_message.content = None
        loop_response.choices = [MagicMock()]
        loop_response.choices[0].message = loop_message

        final_response = MagicMock()
        final_message = MagicMock()
        final_message.tool_calls = None
        final_message.content = "Final answer after max turns."
        final_response.choices = [MagicMock()]
        final_response.choices[0].message = final_message

        client.chat.completions.create.side_effect = [
            loop_response, loop_response, final_response,
        ]

        result = agentic_rag(client, "test", lambda q: [], max_turns=2)
        assert isinstance(result, str)
