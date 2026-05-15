"""Tests for Exercise 02 — Supervisor-Critic Pipeline."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock


def _ensure_openai_mock():
    """Inject a stub openai module so imports work without the real package."""
    try:
        from openai import OpenAI  # noqa: F401
    except (ImportError, AttributeError):
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock
        sys.modules["openai"] = mock_openai


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    _ensure_openai_mock()
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


def _mock_client_json(content: dict):
    """Create a mock OpenAI client that returns a JSON string."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(content)))]
    mock.chat.completions.create.return_value = mock_response
    return mock


def _mock_client_sequence(responses: List[str]):
    """Create a mock client that returns a different response on each call."""
    mock = MagicMock()
    call_idx = 0

    def side_effect(**kwargs):
        nonlocal call_idx
        content = responses[min(call_idx, len(responses) - 1)]
        call_idx += 1
        return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])

    mock.chat.completions.create.side_effect = side_effect
    return mock


# --- CriticAgent tests ---

def test_critic_review_returns_approved_and_feedback():
    """CriticAgent.review returns a dict with 'approved' (bool) and 'feedback' (str)."""
    mod = _import_start()
    client = _mock_client_json({"approved": True, "feedback": "Looks good."})
    critic = mod.CriticAgent(client)

    result = critic.review("What is our heading?", "Heading is 045 mark 2.")
    assert isinstance(result, dict)
    assert "approved" in result
    assert "feedback" in result
    assert isinstance(result["approved"], bool)
    assert isinstance(result["feedback"], str)


def test_critic_review_approved_true():
    """CriticAgent.review correctly parses an approval."""
    mod = _import_start()
    client = _mock_client_json({"approved": True, "feedback": "Accurate."})
    critic = mod.CriticAgent(client)

    result = critic.review("heading?", "045 mark 2")
    assert result["approved"] is True


def test_critic_review_approved_false():
    """CriticAgent.review correctly parses a rejection."""
    mod = _import_start()
    client = _mock_client_json({"approved": False, "feedback": "Missing coordinates."})
    critic = mod.CriticAgent(client)

    result = critic.review("heading?", "We are going forward")
    assert result["approved"] is False
    assert len(result["feedback"]) > 0


def test_critic_defaults_on_bad_json():
    """CriticAgent.review defaults to approved on unparseable JSON."""
    mod = _import_start()
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="not json"))]
    mock.chat.completions.create.return_value = mock_response
    critic = mod.CriticAgent(mock)

    result = critic.review("q", "r")
    assert result["approved"] is True


# --- SupervisorAgent tests ---

def test_supervisor_run_returns_required_keys():
    """SupervisorAgent.run returns department, response, and trace."""
    mod = _import_start()
    responses = [
        json.dumps({"department": "navigation"}),
        "Current heading is 045 mark 2.",
        json.dumps({"approved": True, "feedback": "Accurate."}),
    ]
    client = _mock_client_sequence(responses)
    supervisor = mod.SupervisorAgent(client, max_revisions=2)

    result = supervisor.run("What is our heading?")
    assert isinstance(result, dict)
    assert "department" in result
    assert "response" in result
    assert "trace" in result
    assert isinstance(result["trace"], list)


def test_supervisor_approved_trace_has_three_entries():
    """When critic approves first time, trace has exactly 3 entries."""
    mod = _import_start()
    responses = [
        json.dumps({"department": "engineering"}),
        "Warp core is stable at 98% efficiency.",
        json.dumps({"approved": True, "feedback": "Good."}),
    ]
    client = _mock_client_sequence(responses)
    supervisor = mod.SupervisorAgent(client, max_revisions=2)

    result = supervisor.run("Warp core status?")
    assert len(result["trace"]) == 3


def test_supervisor_rejected_trace_has_revision():
    """When critic rejects, trace includes revision entries."""
    mod = _import_start()
    responses = [
        json.dumps({"department": "science"}),
        "The anomaly is interesting.",
        json.dumps({"approved": False, "feedback": "Too vague, need sensor data."}),
        "Revised: anomaly at coordinates 7.3.2, energy spike of 4.7 terawatts.",
        json.dumps({"approved": True, "feedback": "Much better."}),
    ]
    client = _mock_client_sequence(responses)
    supervisor = mod.SupervisorAgent(client, max_revisions=2)

    result = supervisor.run("Analyse the anomaly")
    assert len(result["trace"]) > 3
    revision_steps = [s for s in result["trace"] if s.get("revision")]
    assert len(revision_steps) >= 1


def test_supervisor_respects_max_revisions():
    """SupervisorAgent stops after max_revisions even if critic keeps rejecting."""
    mod = _import_start()
    responses = [
        json.dumps({"department": "navigation"}),
        "First attempt.",
        json.dumps({"approved": False, "feedback": "Bad."}),
        "Second attempt.",
        json.dumps({"approved": False, "feedback": "Still bad."}),
        "Third attempt.",
        json.dumps({"approved": False, "feedback": "No good."}),
        "Fourth attempt (should not happen).",
    ]
    client = _mock_client_sequence(responses)
    supervisor = mod.SupervisorAgent(client, max_revisions=2)

    result = supervisor.run("heading?")
    critic_steps = [s for s in result["trace"] if s.get("agent") == "critic"]
    assert len(critic_steps) <= 3


def test_supervisor_uses_department_from_classifier():
    """SupervisorAgent uses the department returned by the router."""
    mod = _import_start()
    responses = [
        json.dumps({"department": "engineering"}),
        "Hull at 100%.",
        json.dumps({"approved": True, "feedback": "OK."}),
    ]
    client = _mock_client_sequence(responses)
    supervisor = mod.SupervisorAgent(client, max_revisions=1)

    result = supervisor.run("Hull status?")
    assert result["department"] == "engineering"


# --- run_supervised_query tests ---

def test_run_supervised_query_returns_result():
    """run_supervised_query returns the same structure as SupervisorAgent.run."""
    mod = _import_start()
    responses = [
        json.dumps({"department": "science"}),
        "Nebula analysis complete.",
        json.dumps({"approved": True, "feedback": "Good analysis."}),
    ]
    client = _mock_client_sequence(responses)

    result = mod.run_supervised_query("Analyse the nebula", client, max_revisions=1)
    assert isinstance(result, dict)
    assert "department" in result
    assert "response" in result
    assert "trace" in result
