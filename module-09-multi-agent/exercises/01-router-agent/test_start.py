"""Tests for Exercise 01 — Router + Specialist Agents."""

import importlib
import json
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


def _mock_client(content: str = "Mock response"):
    """Create a mock OpenAI client returning fixed content."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    mock.chat.completions.create.return_value = mock_response
    return mock


# --- classify_query tests ---

def test_classify_returns_valid_department():
    """classify_query returns one of the three valid departments."""
    mod = _import_start()
    client = _mock_client(json.dumps({"department": "navigation"}))
    result = mod.classify_query("What is our heading?", client)
    assert result in mod.DEPARTMENTS


def test_classify_defaults_on_bad_json():
    """classify_query defaults to 'science' on unparseable JSON."""
    mod = _import_start()
    client = _mock_client("not json at all")
    result = mod.classify_query("random query", client)
    assert result == "science"


def test_classify_defaults_on_unknown_department():
    """classify_query defaults to 'science' for unrecognised departments."""
    mod = _import_start()
    client = _mock_client(json.dumps({"department": "weapons"}))
    result = mod.classify_query("fire torpedoes", client)
    assert result == "science"


def test_classify_calls_openai():
    """classify_query calls the OpenAI client."""
    mod = _import_start()
    client = _mock_client(json.dumps({"department": "engineering"}))
    mod.classify_query("hull status?", client)
    assert client.chat.completions.create.called


# --- specialist_agent tests ---

def test_specialist_returns_string():
    """specialist_agent returns a non-empty string."""
    mod = _import_start()
    client = _mock_client("Engine room report: all systems nominal.")
    result = mod.specialist_agent("engineering", "engine status?", client)
    assert isinstance(result, str)
    assert len(result) > 0


def test_specialist_calls_openai():
    """specialist_agent calls the OpenAI client."""
    mod = _import_start()
    client = _mock_client("Response")
    mod.specialist_agent("navigation", "heading?", client)
    assert client.chat.completions.create.called


def test_specialist_uses_correct_prompt():
    """specialist_agent passes the department's system prompt."""
    mod = _import_start()
    client = _mock_client("Response")
    mod.specialist_agent("engineering", "hull status?", client)

    call_args = client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
    system_msg = messages[0]["content"]
    assert "Engineer" in system_msg


def test_specialist_fallback_for_unknown_department():
    """specialist_agent uses science prompt for unknown departments."""
    mod = _import_start()
    client = _mock_client("Response")
    mod.specialist_agent("weapons", "fire!", client)

    call_args = client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
    system_msg = messages[0]["content"]
    assert "Science" in system_msg


# --- route_and_respond tests ---

def test_route_and_respond_returns_dict():
    """route_and_respond returns a dict with department and response."""
    mod = _import_start()
    client = _mock_client(json.dumps({"department": "navigation"}))

    def side_effect(**kwargs):
        messages = kwargs.get("messages", [])
        if any("router" in m.get("content", "").lower() for m in messages):
            return MagicMock(
                choices=[MagicMock(
                    message=MagicMock(content=json.dumps({"department": "navigation"}))
                )]
            )
        return MagicMock(
            choices=[MagicMock(message=MagicMock(content="Heading is 045."))]
        )

    client.chat.completions.create.side_effect = side_effect

    result = mod.route_and_respond("What is our heading?", client)
    assert isinstance(result, dict)
    assert "department" in result
    assert "response" in result
    assert result["department"] in mod.DEPARTMENTS


def test_route_and_respond_calls_openai_twice():
    """route_and_respond makes at least 2 OpenAI calls (classify + specialist)."""
    mod = _import_start()

    call_count = 0

    def side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MagicMock(
                choices=[MagicMock(
                    message=MagicMock(content=json.dumps({"department": "science"}))
                )]
            )
        return MagicMock(
            choices=[MagicMock(message=MagicMock(content="Anomaly detected."))]
        )

    client = MagicMock()
    client.chat.completions.create.side_effect = side_effect

    mod.route_and_respond("Analyse the nebula", client)
    assert call_count >= 2
