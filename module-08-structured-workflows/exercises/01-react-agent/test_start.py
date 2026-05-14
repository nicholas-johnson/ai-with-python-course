"""Tests for Exercise 01: ReAct Agent."""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


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


def test_calculator_basic():
    """calculator returns correct result for simple arithmetic."""
    mod = _import_start()
    result = mod.calculator("2 + 3")
    assert result == "5", f"Expected '5', got '{result}'"


def test_calculator_complex():
    """calculator handles parentheses and decimals."""
    mod = _import_start()
    result = mod.calculator("(10 + 5) * 2")
    assert result == "30", f"Expected '30', got '{result}'"


def test_calculator_rejects_unsafe():
    """calculator rejects expressions with unsafe characters."""
    mod = _import_start()
    result = mod.calculator("__import__('os').system('ls')")
    assert "error" in result.lower() or "unsafe" in result.lower(), (
        "Should reject unsafe expressions"
    )


def test_take_note_and_read_notes():
    """take_note stores notes and read_notes retrieves them."""
    mod = _import_start()
    mod._notes.clear()

    result1 = mod.take_note("first note")
    assert "1" in result1, "Should confirm 1 note saved"

    result2 = mod.take_note("second note")
    assert "2" in result2, "Should confirm 2 notes saved"

    notes = mod.read_notes()
    assert "first note" in notes
    assert "second note" in notes

    mod._notes.clear()


def test_read_notes_empty():
    """read_notes returns a message when no notes exist."""
    mod = _import_start()
    mod._notes.clear()

    notes = mod.read_notes()
    assert "no notes" in notes.lower(), f"Expected 'no notes' message, got '{notes}'"


def test_tool_schemas_defined():
    """TOOL_SCHEMAS is a non-empty list of function schemas."""
    mod = _import_start()
    assert isinstance(mod.TOOL_SCHEMAS, list), "TOOL_SCHEMAS should be a list"
    assert len(mod.TOOL_SCHEMAS) > 0, "TOOL_SCHEMAS should not be empty"
    for schema in mod.TOOL_SCHEMAS:
        assert "type" in schema, "Each schema needs a 'type' key"
        assert "function" in schema, "Each schema needs a 'function' key"
        assert "name" in schema["function"], "Each function needs a 'name'"


def test_run_react_returns_dict():
    """run_react returns a dict with 'answer' and 'trace' keys."""
    mod = _import_start()

    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "The answer is 42."
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    result = mod.run_react("What is 6 * 7?", mock_client, max_steps=3)

    assert isinstance(result, dict), "run_react should return a dict"
    assert "answer" in result, "Result should have 'answer' key"
    assert "trace" in result, "Result should have 'trace' key"
    assert isinstance(result["trace"], list), "Trace should be a list"


def test_run_react_handles_tool_calls():
    """run_react processes tool calls and loops correctly."""
    mod = _import_start()

    mock_client = MagicMock()

    tool_call_msg = MagicMock()
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = "calculator"
    tool_call.function.arguments = json.dumps({"expression": "2 + 2"})
    tool_call_msg.tool_calls = [tool_call]
    tool_call_msg.content = None

    final_msg = MagicMock()
    final_msg.tool_calls = None
    final_msg.content = "The result is 4."

    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=tool_call_msg)]),
        MagicMock(choices=[MagicMock(message=final_msg)]),
    ]

    result = mod.run_react("What is 2 + 2?", mock_client, max_steps=5)

    assert result["answer"] == "The result is 4."
    assert len(result["trace"]) >= 2
    tool_steps = [s for s in result["trace"] if s["type"] == "tool"]
    assert len(tool_steps) == 1
    assert tool_steps[0]["name"] == "calculator"
