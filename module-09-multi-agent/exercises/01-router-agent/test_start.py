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
    """Create a mock OpenAI client whose plain completions return fixed content."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    mock.chat.completions.create.return_value = mock_response
    return mock


def _refusing_client():
    """A mock client whose structured-output call comes back as a refusal."""
    mock = MagicMock()
    message = MagicMock(parsed=None, refusal="I can't help with that.")
    mock.chat.completions.parse.return_value = MagicMock(choices=[MagicMock(message=message)])
    return mock


# --- classify_query tests ---

def test_classify_returns_valid_department(fake_parse):
    """classify_query returns the department from the parsed Route."""
    mod = _import_start()
    client = MagicMock()
    client.chat.completions.parse.side_effect = fake_parse(json.dumps({"department": "tactical"}))
    result = mod.classify_query("Raise shields!", client)
    assert result == "tactical"


def test_classify_uses_route_schema(fake_parse):
    """classify_query asks for structured output with the Route model."""
    mod = _import_start()
    client = MagicMock()
    client.chat.completions.parse.side_effect = fake_parse(json.dumps({"department": "comms"}))
    mod.classify_query("Any signals?", client)
    assert client.chat.completions.parse.call_args.kwargs["response_format"] is mod.Route


def test_route_schema_rejects_unknown_department():
    """The Literal type means an unknown department can't be parsed."""
    mod = _import_start()
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        mod.Route(department="catering")


def test_classify_defaults_on_refusal():
    """classify_query defaults to 'medical' when the model refuses."""
    mod = _import_start()
    result = mod.classify_query("random query", _refusing_client())
    assert result == "medical"


# --- specialist_agent tests ---

def test_specialist_returns_string():
    """specialist_agent returns a non-empty string."""
    mod = _import_start()
    client = _mock_client("Shields holding at 94%, no incoming threats detected.")
    result = mod.specialist_agent("tactical", "shield status?", client)
    assert isinstance(result, str)
    assert len(result) > 0


def test_specialist_calls_openai():
    """specialist_agent calls the OpenAI client."""
    mod = _import_start()
    client = _mock_client("Response")
    mod.specialist_agent("comms", "any signals?", client)
    assert client.chat.completions.create.called


def test_specialist_uses_correct_prompt():
    """specialist_agent passes the department's system prompt."""
    mod = _import_start()
    client = _mock_client("Response")
    mod.specialist_agent("tactical", "shield status?", client)

    call_args = client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
    system_msg = messages[0]["content"]
    assert "Tactical" in system_msg


def test_specialist_fallback_for_unknown_department():
    """specialist_agent uses medical prompt for unknown departments."""
    mod = _import_start()
    client = _mock_client("Response")
    mod.specialist_agent("catering", "what's for lunch?", client)

    call_args = client.chat.completions.create.call_args
    messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
    system_msg = messages[0]["content"]
    assert "Medical" in system_msg


# --- route_and_respond tests ---

def test_route_and_respond_returns_dict(fake_parse):
    """route_and_respond returns a dict with department and response."""
    mod = _import_start()
    client = _mock_client("Shields at full power.")
    client.chat.completions.parse.side_effect = fake_parse(json.dumps({"department": "tactical"}))

    result = mod.route_and_respond("Raise shields!", client)
    assert isinstance(result, dict)
    assert result["department"] == "tactical"
    assert result["response"] == "Shields at full power."


def test_route_and_respond_classifies_then_answers(fake_parse):
    """route_and_respond makes a structured call (classify) and a text call (specialist)."""
    mod = _import_start()
    client = _mock_client("Crew vitals are stable.")
    client.chat.completions.parse.side_effect = fake_parse(json.dumps({"department": "medical"}))

    mod.route_and_respond("Crew health report", client)
    assert client.chat.completions.parse.call_count == 1
    assert client.chat.completions.create.call_count >= 1
