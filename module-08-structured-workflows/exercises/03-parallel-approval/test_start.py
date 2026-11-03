"""Tests for Exercise 03: Parallel Plans and Approval Gates."""

import asyncio
import importlib
import json
import sys
from dataclasses import fields
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


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
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _step(
    mod,
    number,
    *,
    tool="research_destination",
    depends_on=None,
    gated=False,
    status="pending",
):
    return mod.PlanStep(
        step_number=number,
        description=f"step {number}",
        tool=tool,
        depends_on=depends_on or [],
        requires_approval=gated,
        status=status,
    )


def test_plan_step_has_scheduling_fields():
    """PlanStep carries depends_on and requires_approval alongside runtime state."""
    mod = _import_start()
    field_names = {f.name for f in fields(mod.PlanStep)}
    for expected in (
        "step_number",
        "description",
        "tool",
        "depends_on",
        "requires_approval",
        "status",
        "result",
    ):
        assert expected in field_names, f"PlanStep is missing '{expected}'"


def test_generate_plan_gates_irreversible_steps(fake_parse):
    """requires_approval is set by code from IRREVERSIBLE, not taken from the model."""
    mod = _import_start()

    mock_client = MagicMock()
    plan_json = json.dumps({
        "steps": [
            {
                "step_number": 1,
                "description": "Research Lisbon",
                "tool": "research_destination",
                "depends_on": [],
            },
            {
                "step_number": 2,
                "description": "Find a flight to Lisbon",
                "tool": "find_flight",
                "depends_on": [],
            },
            {
                "step_number": 3,
                "description": "Book the flight",
                "tool": "book_flight",
                "depends_on": [2],
            },
        ]
    })
    mock_client.responses.parse.side_effect = fake_parse(plan_json)

    plan = mod.generate_plan("Plan a trip to Lisbon", mock_client)

    assert len(plan) == 3
    assert plan[0].requires_approval is False
    assert plan[1].requires_approval is False
    assert plan[2].requires_approval is True, "book_flight is irreversible and must be gated"
    assert plan[2].depends_on == [2], "depends_on must survive the conversion"


def test_dependency_levels_groups_independent_steps():
    """Steps with no dependencies all land in the first wave."""
    mod = _import_start()
    steps = [_step(mod, n) for n in (1, 2, 3)]

    levels = mod.dependency_levels(steps)

    assert len(levels) == 1, "Independent steps should run in a single wave"
    assert {s.step_number for s in levels[0]} == {1, 2, 3}


def test_dependency_levels_respects_order():
    """A fan-out followed by a join produces the right waves."""
    mod = _import_start()
    steps = [
        _step(mod, 1),
        _step(mod, 2),
        _step(mod, 3, depends_on=[1, 2]),
    ]

    levels = mod.dependency_levels(steps)

    assert [sorted(s.step_number for s in wave) for wave in levels] == [[1, 2], [3]]


def test_dependency_levels_survives_a_cycle():
    """A circular plan must not hang the scheduler."""
    mod = _import_start()
    steps = [_step(mod, 1, depends_on=[2]), _step(mod, 2, depends_on=[1])]

    levels = mod.dependency_levels(steps)

    assert sum(len(w) for w in levels) == 2, "Every step should still be scheduled"


def test_run_plan_blocks_on_unapproved_step(tmp_path):
    """The gated step does not execute until a human approves it."""
    mod = _import_start()
    steps = [
        _step(mod, 1, tool="find_flight"),
        _step(mod, 2, tool="book_flight", depends_on=[1], gated=True),
    ]

    executed = []

    async def fake_execute(description, context, client):
        executed.append(description)
        return f"result for {description}"

    with patch.object(mod, "CHECKPOINT", tmp_path / "state.json"), \
         patch.object(mod, "execute_step", fake_execute):
        status = asyncio.run(mod.run_plan("goal", steps, [], AsyncMock()))

    assert status == "awaiting_approval"
    assert executed == ["step 1"], "Only the ungated step should have run"
    assert steps[1].status == "awaiting_approval"


def test_run_plan_resumes_without_repeating_work(tmp_path):
    """After approval, finished steps are skipped and the gated step runs once."""
    mod = _import_start()
    steps = [
        _step(mod, 1, tool="find_flight", status="done"),
        _step(mod, 2, tool="book_flight", depends_on=[1], gated=True),
    ]
    steps[0].result = "FR1823"

    executed = []

    async def fake_execute(description, context, client):
        executed.append(description)
        return f"result for {description}"

    with patch.object(mod, "CHECKPOINT", tmp_path / "state.json"), \
         patch.object(mod, "execute_step", fake_execute):
        status = asyncio.run(mod.run_plan("goal", steps, [2], AsyncMock()))

    assert status == "complete"
    assert executed == ["step 2"], "The completed step must not run again"
    assert steps[1].status == "done"


def test_run_plan_runs_a_wave_concurrently(tmp_path):
    """Independent steps overlap instead of running one after another."""
    mod = _import_start()
    steps = [_step(mod, n) for n in (1, 2, 3)]

    async def slow_execute(description, context, client):
        await asyncio.sleep(0.2)
        return "done"

    with patch.object(mod, "CHECKPOINT", tmp_path / "state.json"), \
         patch.object(mod, "execute_step", slow_execute):

        async def _timed():
            start = asyncio.get_running_loop().time()
            await mod.run_plan("goal", steps, [], AsyncMock())
            return asyncio.get_running_loop().time() - start

        elapsed = asyncio.run(_timed())

    assert elapsed < 0.5, (
        f"Three 0.2s steps took {elapsed:.2f}s — they ran serially, not concurrently"
    )


def test_checkpoint_round_trips(tmp_path):
    """State written to disk can be read back with statuses and results intact."""
    mod = _import_start()
    steps = [
        _step(mod, 1, status="done"),
        _step(mod, 2, tool="book_flight", depends_on=[1], gated=True),
    ]
    steps[0].result = "Lisbon is warm in May"

    with patch.object(mod, "CHECKPOINT", tmp_path / "state.json"):
        mod.save_state("a goal", steps, [2])
        restored = mod.load_state()

    assert restored is not None, "load_state should return the saved state"
    goal, loaded_steps, approved = restored
    assert goal == "a goal"
    assert approved == [2]
    assert loaded_steps[0].status == "done"
    assert loaded_steps[0].result == "Lisbon is warm in May"
    assert loaded_steps[1].requires_approval is True
    assert loaded_steps[1].depends_on == [1]


def test_load_state_returns_none_without_a_checkpoint(tmp_path):
    """A missing checkpoint is not an error."""
    mod = _import_start()
    with patch.object(mod, "CHECKPOINT", tmp_path / "nothing-here.json"):
        assert mod.load_state() is None
