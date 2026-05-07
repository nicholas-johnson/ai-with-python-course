"""Tests for Exercise 01 — Chat Loop."""

import pytest

from start import ChatBot


class FakeLLM:
    def __init__(self, responses: list[str] | None = None):
        self._responses = list(responses or ["Default response."])
        self._index = 0

    def chat(self, messages: list[dict]) -> str:
        resp = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return resp


class TestChatBot:
    def test_initial_history_has_system_prompt(self):
        bot = ChatBot(llm=FakeLLM(), system_prompt="Test prompt")
        history = bot.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "system"
        assert history[0]["content"] == "Test prompt"

    def test_chat_returns_response(self):
        bot = ChatBot(llm=FakeLLM(["Hello, Engineer."]))
        response = bot.chat("Hi")
        assert response == "Hello, Engineer."

    def test_chat_appends_to_history(self):
        bot = ChatBot(llm=FakeLLM(["Response 1", "Response 2"]))
        bot.chat("First")
        bot.chat("Second")

        history = bot.get_history()
        assert len(history) == 5  # system + 2*(user + assistant)
        assert history[1]["role"] == "user"
        assert history[1]["content"] == "First"
        assert history[2]["role"] == "assistant"
        assert history[2]["content"] == "Response 1"
        assert history[3]["role"] == "user"
        assert history[3]["content"] == "Second"
        assert history[4]["role"] == "assistant"

    def test_clear_resets_history(self):
        bot = ChatBot(llm=FakeLLM(["R1"]))
        bot.chat("Hello")
        assert len(bot.get_history()) == 3

        bot.clear()
        history = bot.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "system"

    def test_chat_after_clear(self):
        bot = ChatBot(llm=FakeLLM(["R1", "R2"]))
        bot.chat("First")
        bot.clear()
        response = bot.chat("After clear")

        assert response == "R2"
        history = bot.get_history()
        assert len(history) == 3

    def test_llm_receives_full_history(self):
        seen_messages = []

        class SpyLLM:
            def chat(self, messages):
                seen_messages.append(len(messages))
                return "ok"

        bot = ChatBot(llm=SpyLLM())
        bot.chat("A")
        bot.chat("B")
        assert seen_messages == [2, 4]  # system+user, then system+user+assistant+user
