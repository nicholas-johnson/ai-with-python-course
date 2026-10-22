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
    mock_response.output_text = content
    mock.responses.create.return_value = mock_response
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

    assert client.responses.create.call_count >= 4


# --- judge tests ---


def test_judge_returns_winner_and_reasoning(fake_parse):
    """judge returns a dict with 'winner' and 'reasoning' keys."""
    mod = _import_start()
    client = MagicMock()
    client.responses.parse.side_effect = fake_parse(
        json.dumps({"winner": "skeptic", "reasoning": "More evidence cited."})
    )
    result = mod.judge(
        "Should we proceed?",
        "It's safe to go.",
        "Too many unknowns.",
        client,
    )

    assert isinstance(result, dict)
    assert result["winner"] == "skeptic"
    assert "reasoning" in result
    assert isinstance(result["reasoning"], str)


def test_judge_defaults_on_refusal():
    """judge defaults to 'advocate' when the model refuses (parsed is None)."""
    mod = _import_start()
    client = MagicMock()
    # The model refused: no parsed output.
    client.responses.parse.return_value = MagicMock(output_parsed=None, output_text="")
    result = mod.judge("Question?", "For.", "Against.", client)

    assert result["winner"] == "advocate"


# --- consensus_vote tests ---


def test_consensus_vote_returns_correct_structure(fake_parse):
    """consensus_vote returns responses, winner, and votes."""
    mod = _import_start()

    client = _mock_client("Specialist answer.")
    client.responses.parse.side_effect = fake_parse(json.dumps({"vote": "medical"}))

    result = mod.consensus_vote("What caused the power surge?", client)

    assert isinstance(result, dict)
    assert "responses" in result
    assert "winner" in result
    assert "votes" in result
    assert isinstance(result["responses"], list)
    assert len(result["responses"]) == len(mod.DEPARTMENTS)
    assert result["winner"] == "medical"
    assert result["votes"]["medical"] == len(mod.DEPARTMENTS)


def test_consensus_vote_responses_have_department_and_response(fake_parse):
    """Each response entry has department and response keys."""
    mod = _import_start()

    client = _mock_client("Specialist says...")
    client.responses.parse.side_effect = fake_parse(json.dumps({"vote": "tactical"}))

    result = mod.consensus_vote("Status report", client)

    for entry in result["responses"]:
        assert "department" in entry
        assert "response" in entry
        assert entry["department"] in mod.DEPARTMENTS
