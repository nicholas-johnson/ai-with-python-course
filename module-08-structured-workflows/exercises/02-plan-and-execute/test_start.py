"""Tests for Exercise 02: Plan-and-Execute."""

import importlib
import json
import sys
from dataclasses import fields
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


def test_plan_step_dataclass():
    """PlanStep has the required fields."""
    mod = _import_start()
    step = mod.PlanStep(step_number=1, description="test step")
    assert step.step_number == 1
    assert step.description == "test step"
    assert step.status == "pending"
    assert step.result == ""

    field_names = {f.name for f in fields(mod.PlanStep)}
    assert "step_number" in field_names
    assert "description" in field_names
    assert "status" in field_names
    assert "result" in field_names


def test_generate_plan_returns_list():
    """generate_plan returns a list of PlanStep objects."""
    mod = _import_start()

    mock_client = MagicMock()
    plan_json = json.dumps({
        "steps": [
            {"step_number": 1, "description": "Search for info"},
            {"step_number": 2, "description": "Calculate result"},
            {"step_number": 3, "description": "Summarize findings"},
        ]
    })
    mock_message = MagicMock()
    mock_message.content = plan_json
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=mock_message)]
    )

    plan = mod.generate_plan("test query", mock_client)

    assert isinstance(plan, list), "generate_plan should return a list"
    assert len(plan) == 3, f"Expected 3 steps, got {len(plan)}"
    assert all(isinstance(s, mod.PlanStep) for s in plan)
    assert plan[0].description == "Search for info"
    assert plan[0].status == "pending"


def test_execute_step_returns_result():
    """execute_step returns a result dict from run_react."""
    mod = _import_start()

    mock_client = MagicMock()

    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "Step result: found the data."
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=mock_message)]
    )

    step = mod.PlanStep(step_number=1, description="Search for data")
    result = mod.execute_step(step, [], mock_client)

    assert isinstance(result, dict), "execute_step should return a dict"
    assert "answer" in result, "Result should have 'answer' key"
    assert "trace" in result, "Result should have 'trace' key"


def test_plan_and_execute_returns_answer_and_plan():
    """plan_and_execute returns a dict with 'answer' and 'plan' keys."""
    mod = _import_start()

    mock_client = MagicMock()

    plan_json = json.dumps({
        "steps": [
            {"step_number": 1, "description": "Do the thing"},
        ]
    })

    plan_message = MagicMock()
    plan_message.content = plan_json

    react_message = MagicMock()
    react_message.tool_calls = None
    react_message.content = "Done: the thing is done."

    summary_message = MagicMock()
    summary_message.content = "Final answer: the thing was done successfully."

    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=plan_message)]),
        MagicMock(choices=[MagicMock(message=react_message)]),
        MagicMock(choices=[MagicMock(message=summary_message)]),
    ]

    result = mod.plan_and_execute("Do the thing", mock_client)

    assert isinstance(result, dict), "plan_and_execute should return a dict"
    assert "answer" in result, "Result should have 'answer' key"
    assert "plan" in result, "Result should have 'plan' key"
    assert isinstance(result["plan"], list), "Plan should be a list"
