"""Tests for Exercise 03 — Debate + Consensus."""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
    if str(ex_dir) not in sys.path:
        sys.path.insert(0, str(ex_dir))

    for name in ("start", "solution"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            if hasattr(mod, "debate"):
                return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _mock_client(content: str = "Mock response"):
    """Create a mock OpenAI client returning fixed content."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    mock.chat.completions.create.return_value = mock_response
    return mock


# --- debate tests ---


def test_debate_returns_list_of_rounds():
    """debate returns a list of dicts with round/advocate/skeptic keys."""
    mod = _import_start()
    client = _mock_client("A compelling argument.")
    result = mod.debate("Should we enter the nebula?", client, rounds=2)

    assert isinstance(result, list)
    assert len(result) == 2
    for entry in result:
        assert "round" in entry
        assert "advocate" in entry
        assert "skeptic" in entry
        assert isinstance(entry["advocate"], str)
        assert isinstance(entry["skeptic"], str)


def test_debate_respects_rounds_parameter():
    """debate produces exactly N rounds when rounds=N."""
    mod = _import_start()
    client = _mock_client("Argument text.")
    result = mod.debate("Should we reroute?", client, rounds=3)

    assert len(result) == 3
    assert result[0]["round"] == 1
    assert result[1]["round"] == 2
    assert result[2]["round"] == 3


def test_debate_calls_openai():
    """debate makes LLM calls (at least 2 per round: advocate + skeptic)."""
    mod = _import_start()
    client = _mock_client("Debate point.")
    mod.debate("Is the anomaly dangerous?", client, rounds=2)

    assert client.chat.completions.create.call_count >= 4


# --- judge tests ---


def test_judge_returns_winner_and_reasoning():
    """judge returns a dict with 'winner' and 'reasoning' keys."""
    mod = _import_start()
    client = _mock_client(
        json.dumps({"winner": "skeptic", "reasoning": "More evidence cited."})
    )
    result = mod.judge(
        "Should we proceed?",
        "It's safe to go.",
        "Too many unknowns.",
        client,
    )

    assert isinstance(result, dict)
    assert result["winner"] in ("advocate", "skeptic")
    assert "reasoning" in result
    assert isinstance(result["reasoning"], str)


def test_judge_defaults_on_bad_json():
    """judge defaults to 'advocate' when JSON parsing fails."""
    mod = _import_start()
    client = _mock_client("not valid json")
    result = mod.judge("Question?", "For.", "Against.", client)

    assert result["winner"] == "advocate"


# --- consensus_vote tests ---


def test_consensus_vote_returns_correct_structure():
    """consensus_vote returns responses, winner, and votes."""
    mod = _import_start()

    call_count = [0]

    def side_effect(**kwargs):
        call_count[0] += 1
        messages = kwargs.get("messages", [])
        is_vote = any("voting agent" in m.get("content", "").lower() for m in messages)
        if is_vote:
            return MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=json.dumps({"vote": "science"})
                        )
                    )
                ]
            )
        return MagicMock(
            choices=[MagicMock(message=MagicMock(content="Specialist answer."))]
        )

    client = MagicMock()
    client.chat.completions.create.side_effect = side_effect

    result = mod.consensus_vote("What caused the power surge?", client)

    assert isinstance(result, dict)
    assert "responses" in result
    assert "winner" in result
    assert "votes" in result
    assert isinstance(result["responses"], list)
    assert len(result["responses"]) == len(mod.DEPARTMENTS)
    assert result["winner"] in mod.DEPARTMENTS
    assert isinstance(result["votes"], dict)


def test_consensus_vote_responses_have_department_and_response():
    """Each response entry has department and response keys."""
    mod = _import_start()
    client = _mock_client("Response text.")

    client.chat.completions.create.side_effect = None
    responses = []

    def side_effect(**kwargs):
        messages = kwargs.get("messages", [])
        is_vote = any("voting agent" in m.get("content", "").lower() for m in messages)
        if is_vote:
            return MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=json.dumps({"vote": "navigation"})
                        )
                    )
                ]
            )
        return MagicMock(
            choices=[MagicMock(message=MagicMock(content="Specialist says..."))]
        )

    client = MagicMock()
    client.chat.completions.create.side_effect = side_effect

    result = mod.consensus_vote("Status report", client)

    for entry in result["responses"]:
        assert "department" in entry
        assert "response" in entry
        assert entry["department"] in mod.DEPARTMENTS
