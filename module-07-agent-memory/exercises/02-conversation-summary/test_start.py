"""Tests for Exercise 02 — Conversation Summary."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
    for name in ("start", "solution"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _mock_client(summary_text="The user discussed various topics."):
    """Create a mock OpenAI client that returns a fixed summary."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=summary_text))
    ]
    mock.chat.completions.create.return_value = mock_response
    return mock


# --- summarise_turns tests ---

def test_summarise_turns_returns_string():
    """summarise_turns returns a non-empty string."""
    mod = _import_start()
    client = _mock_client("Summary of the conversation.")

    turns = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thanks!"},
        {"role": "user", "content": "Tell me about Python."},
        {"role": "assistant", "content": "Python is a great language."},
    ]

    result = mod.summarise_turns(turns, client)
    assert isinstance(result, str)
    assert len(result) > 0


def test_summarise_turns_calls_openai():
    """summarise_turns calls the OpenAI client."""
    mod = _import_start()
    client = _mock_client()

    turns = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    mod.summarise_turns(turns, client)
    assert client.chat.completions.create.called


# --- SmartSessionMemory tests ---

def test_smart_session_basic_add():
    """SmartSessionMemory adds messages normally below threshold."""
    mod = _import_start()
    session = mod.SmartSessionMemory(
        max_turns=30, summarise_threshold=10, client=_mock_client()
    )

    session.add({"role": "user", "content": "hello"})
    session.add({"role": "assistant", "content": "hi"})

    msgs = session.get_messages()
    assert len(msgs) == 2


def test_smart_session_triggers_summarisation():
    """SmartSessionMemory summarises when exceeding threshold."""
    mod = _import_start()
    client = _mock_client("Conversation summary here.")
    session = mod.SmartSessionMemory(
        max_turns=30, summarise_threshold=6, client=client
    )

    for i in range(8):
        role = "user" if i % 2 == 0 else "assistant"
        session.add({"role": role, "content": f"message {i}"})

    msgs = session.get_messages()
    assert len(msgs) < 8
    assert client.chat.completions.create.called


def test_smart_session_preserves_recent_messages():
    """After summarisation, recent messages are preserved."""
    mod = _import_start()
    client = _mock_client("Summary of old messages.")
    session = mod.SmartSessionMemory(
        max_turns=30, summarise_threshold=6, client=client
    )

    for i in range(8):
        role = "user" if i % 2 == 0 else "assistant"
        session.add({"role": role, "content": f"message {i}"})

    msgs = session.get_messages()
    contents = [m["content"] for m in msgs]
    assert any("message 7" in c for c in contents)


def test_smart_session_stores_summary():
    """SmartSessionMemory stores the summary text."""
    mod = _import_start()
    client = _mock_client("Important conversation details.")
    session = mod.SmartSessionMemory(
        max_turns=30, summarise_threshold=6, client=client
    )

    for i in range(8):
        role = "user" if i % 2 == 0 else "assistant"
        session.add({"role": role, "content": f"message {i}"})

    summary = session.get_summary()
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_smart_session_no_summarise_without_client():
    """SmartSessionMemory does not summarise if no client is provided."""
    mod = _import_start()
    session = mod.SmartSessionMemory(
        max_turns=30, summarise_threshold=4, client=None
    )

    for i in range(6):
        role = "user" if i % 2 == 0 else "assistant"
        session.add({"role": role, "content": f"message {i}"})

    msgs = session.get_messages()
    assert len(msgs) == 6
