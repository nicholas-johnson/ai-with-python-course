"""Tests for Exercise 03 — Prompt Engineering."""

import json
import os
import re
from unittest.mock import MagicMock

import pytest

from start import (
    BASE_PROMPTS,
    CHALLENGES,
    bullet_prompt,
    few_shot_prompt,
    haiku_prompt,
    json_prompt,
    pirate_prompt,
    refusal_prompt,
    run_prompt,
)


# ---------------------------------------------------------------------------
# Structural tests (no API key needed)
# ---------------------------------------------------------------------------

class TestBasePrompts:
    def test_has_expected_keys(self):
        expected = {"concise", "ship_ai", "step_by_step", "translator", "classifier"}
        assert expected == set(BASE_PROMPTS.keys())

    def test_all_prompts_are_nonempty_strings(self):
        for name, prompt in BASE_PROMPTS.items():
            assert isinstance(prompt, str), f"BASE_PROMPTS['{name}'] is not a string"
            assert len(prompt) > 10, f"BASE_PROMPTS['{name}'] is too short"


class TestChallengeRegistry:
    def test_has_expected_challenges(self):
        expected = {"pirate", "bullets", "json", "haiku", "refusal", "few_shot"}
        assert expected == set(CHALLENGES.keys())

    def test_each_entry_has_function_and_message(self):
        for name, (fn, msg) in CHALLENGES.items():
            assert callable(fn), f"CHALLENGES['{name}'] function is not callable"
            assert isinstance(msg, str) and len(msg) > 0, (
                f"CHALLENGES['{name}'] message is empty"
            )


class TestChallengeFunctions:
    """Each challenge function should return a non-empty string."""

    @pytest.mark.parametrize("fn", [
        pirate_prompt, bullet_prompt, json_prompt,
        haiku_prompt, refusal_prompt, few_shot_prompt,
    ])
    def test_returns_nonempty_string(self, fn):
        result = fn()
        assert result is not None, f"{fn.__name__}() returned None — implement it!"
        assert isinstance(result, str), f"{fn.__name__}() must return a string"
        assert len(result) > 10, f"{fn.__name__}() prompt is too short to be useful"


class TestRunPrompt:
    def test_calls_api_and_returns_text(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="mocked response"))
        ]
        result = run_prompt(client, "You are helpful.", "Hello")
        assert result == "mocked response"

    def test_passes_system_and_user_messages(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="ok"))
        ]
        run_prompt(client, "Be concise.", "What is 2+2?")

        call_kwargs = client.chat.completions.create.call_args
        kw = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
        messages = kw["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be concise."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "What is 2+2?"


# ---------------------------------------------------------------------------
# Integration tests (require OPENAI_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="No OPENAI_API_KEY set",
)
class TestIntegration:
    @pytest.fixture(scope="class")
    def client(self):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        return OpenAI()

    def test_pirate_prompt(self, client):
        prompt = pirate_prompt()
        result = run_prompt(client, prompt, "Tell me about the weather today.")
        lower = result.lower()
        pirate_words = ["arr", "matey", "ye", "ahoy", "seas", "treasure", "cap'n"]
        assert any(w in lower for w in pirate_words), (
            f"Expected pirate language, got: {result}"
        )

    def test_bullet_prompt(self, client):
        prompt = bullet_prompt()
        result = run_prompt(client, prompt, "What are the benefits of exercise?")
        lines = [l for l in result.strip().splitlines() if l.strip()]
        bullet_lines = [l for l in lines if l.strip().startswith("- ")]
        assert len(bullet_lines) >= 2, f"Expected bullet points, got: {result}"
        assert len(bullet_lines) == len(lines), (
            f"Expected all lines to be bullets, got: {result}"
        )

    def test_json_prompt(self, client):
        prompt = json_prompt()
        result = run_prompt(client, prompt, "What is the capital of France?")
        raw = result.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        assert "answer" in data, f"Expected 'answer' key in JSON, got: {data}"

    def test_haiku_prompt(self, client):
        prompt = haiku_prompt()
        result = run_prompt(client, prompt, "Write about the ocean.")
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) == 3, f"Expected exactly 3 lines, got {len(lines)}: {result}"

    def test_refusal_off_topic(self, client):
        prompt = refusal_prompt()
        result = run_prompt(client, prompt, "How do I bake a chocolate cake?")
        lower = result.lower()
        assert any(phrase in lower for phrase in [
            "only help with space",
            "only answer questions about space",
            "can only assist with space",
            "only help with astronomy",
            "outside my scope",
            "cannot help with",
            "can't help with",
        ]), f"Expected refusal for off-topic question, got: {result}"

    def test_refusal_on_topic(self, client):
        prompt = refusal_prompt()
        result = run_prompt(client, prompt, "How far is Mars from Earth?")
        assert len(result) > 20, f"Expected a real answer about Mars, got: {result}"
        lower = result.lower()
        assert "only help with" not in lower, (
            f"Should NOT refuse an astronomy question, got: {result}"
        )

    def test_few_shot_prompt(self, client):
        prompt = few_shot_prompt()
        result = run_prompt(
            client, prompt, "The oxygen recycler is making a strange noise."
        )
        assert re.match(r"^[A-Z]+:", result.strip()), (
            f"Expected 'CATEGORY: explanation' format, got: {result}"
        )
