"""Tests for Exercise 01 — First Chat."""

import os
from unittest.mock import MagicMock

import pytest

from start import MODEL, SYSTEM_PROMPT, chat


# ---------------------------------------------------------------------------
# chat() tests (mocked client)
# ---------------------------------------------------------------------------

class TestChat:
    def test_returns_response_text(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Hello, Commander."))
        ]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Hi"},
        ]
        result = chat(client, messages)

        assert result == "Hello, Commander."

    def test_passes_messages_to_api(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="ok"))
        ]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "test"},
        ]
        chat(client, messages)

        client.chat.completions.create.assert_called_once()
        call_kwargs = client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("messages") == messages or call_kwargs[1].get("messages") == messages

    def test_uses_correct_model(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="ok"))
        ]
        chat(client, [{"role": "user", "content": "test"}])

        call_kwargs = client.chat.completions.create.call_args
        used_model = call_kwargs.kwargs.get("model") or call_kwargs[1].get("model")
        assert used_model == MODEL


# ---------------------------------------------------------------------------
# main() conversation flow tests
# ---------------------------------------------------------------------------

class TestMainFlow:
    def test_messages_grow_with_conversation(self):
        """Verify that calling chat twice grows the messages list correctly."""
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Response"))
        ]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        messages.append({"role": "user", "content": "Hello"})
        resp = chat(client, messages)
        messages.append({"role": "assistant", "content": resp})

        messages.append({"role": "user", "content": "Follow up"})
        resp = chat(client, messages)
        messages.append({"role": "assistant", "content": resp})

        assert len(messages) == 5  # system + 2*(user + assistant)
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
        assert messages[4]["role"] == "assistant"


# ---------------------------------------------------------------------------
# Integration test (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="No OPENAI_API_KEY set",
)
class TestIntegration:
    def test_live_chat(self):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        client = OpenAI()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Say hello in exactly 3 words."},
        ]
        result = chat(client, messages)

        assert isinstance(result, str)
        assert len(result) > 0
