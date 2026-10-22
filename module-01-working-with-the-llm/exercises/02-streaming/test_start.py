"""Tests for Exercise 02 — Streaming Chat."""

import os
from unittest.mock import MagicMock

import pytest

from start import MODEL, stream_response


# ---------------------------------------------------------------------------
# Helpers to build mock streaming responses
# ---------------------------------------------------------------------------

def _make_event(delta=None):
    """Build a mock Responses API stream event.

    None stands for a non-text event (response.created, response.completed, ...).
    """
    if delta is None:
        return MagicMock(type="response.in_progress")
    return MagicMock(type="response.output_text.delta", delta=delta)


def _make_stream(tokens: list[str | None]):
    """Build a mock streaming response (iterable of events)."""
    return [_make_event(t) for t in tokens]


# ---------------------------------------------------------------------------
# stream_response() tests
# ---------------------------------------------------------------------------

class TestStreamResponse:
    def test_assembles_full_text(self, capsys):
        client = MagicMock()
        client.responses.create.return_value = _make_stream([
            "Hello", ", ", "Commander", ".",
        ])
        result = stream_response(client, [{"role": "user", "content": "Hi"}])

        assert result == "Hello, Commander."

    def test_skips_non_text_events(self, capsys):
        client = MagicMock()
        client.responses.create.return_value = _make_stream([
            None, "Hi", None, " there", None,
        ])
        result = stream_response(client, [{"role": "user", "content": "test"}])

        assert result == "Hi there"

    def test_prints_tokens_to_stdout(self, capsys):
        client = MagicMock()
        client.responses.create.return_value = _make_stream([
            "Word1", " Word2",
        ])
        stream_response(client, [{"role": "user", "content": "test"}])

        captured = capsys.readouterr()
        assert "Word1" in captured.out
        assert "Word2" in captured.out

    def test_calls_api_with_stream_true(self):
        client = MagicMock()
        client.responses.create.return_value = _make_stream(["ok"])
        stream_response(client, [{"role": "user", "content": "test"}])

        call_kwargs = client.responses.create.call_args
        kw = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
        assert kw.get("stream") is True

    def test_uses_correct_model(self):
        client = MagicMock()
        client.responses.create.return_value = _make_stream(["ok"])
        stream_response(client, [{"role": "user", "content": "test"}])

        call_kwargs = client.responses.create.call_args
        kw = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
        assert kw.get("model") == MODEL

    def test_empty_stream_returns_empty_string(self, capsys):
        client = MagicMock()
        client.responses.create.return_value = _make_stream([None, None])
        result = stream_response(client, [{"role": "user", "content": "test"}])

        assert result == ""


# ---------------------------------------------------------------------------
# Integration test (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="No OPENAI_API_KEY set",
)
class TestIntegration:
    def test_live_streaming(self, capsys):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        client = OpenAI()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 3 words."},
        ]
        result = stream_response(client, messages)

        assert isinstance(result, str)
        assert len(result) > 0
