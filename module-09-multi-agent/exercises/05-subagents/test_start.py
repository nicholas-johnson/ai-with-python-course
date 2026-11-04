"""Tests for Exercise 05 — Spawned Subagents."""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


def _ensure_deps():
    """Stub optional imports so tests run without a full venv."""
    try:
        from dotenv import load_dotenv  # noqa: F401
    except ImportError:
        dotenv = MagicMock()
        dotenv.load_dotenv = lambda *a, **k: None
        sys.modules["dotenv"] = dotenv
    try:
        from openai import AsyncOpenAI  # noqa: F401
    except (ImportError, AttributeError):
        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI = MagicMock
        sys.modules["openai"] = mock_openai


def _import_start():
    """Import solution.py (or start.py) as a module."""
    _ensure_deps()
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
            if hasattr(mod, "fan_out"):
                return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


MOD = _import_start()


def _tool_call(call_id: str, name: str, arguments: str):
    """A mock function_call output item (Responses API shape)."""
    call = MagicMock(type="function_call", call_id=call_id, arguments=arguments)
    call.name = name  # MagicMock(name=...) would name the mock, not set .name
    return call


def _report(claim="Window holds.", window_hours=8.0, confidence=0.9, evidence=None):
    return MOD.SubagentReport(
        claim=claim,
        evidence=evidence or ["LOG-081"],
        window_hours=window_hours,
        confidence=confidence,
    )


def _parsed_response(report, tool_calls=None):
    """A mock responses.parse result: function_call items in .output, model in .output_parsed."""
    return MagicMock(output=list(tool_calls or []), output_parsed=report, output_text="")


def _text_response(content="", tool_calls=None):
    """A mock responses.create result."""
    return MagicMock(output=list(tool_calls or []), output_text=content)


def _finding(department, claim="Window holds.", window_hours=8.0, confidence=0.9, raw_chars=0):
    return MOD.Finding(
        brief=MOD.Brief(department, f"{department} brief"),
        report=_report(claim=claim, window_hours=window_hours, confidence=confidence),
        raw_chars=raw_chars,
    )


def _subagent_client(report=None, tool_calls=None):
    client = MagicMock()
    client.responses.parse = AsyncMock(
        return_value=_parsed_response(report or _report(), tool_calls)
    )
    return client


# --- build_task_brief ---


def test_build_task_brief_has_system_and_user():
    messages = MOD.build_task_brief("medical", "How many survivors?")
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Medical" in messages[0]["content"] or "medical" in messages[0]["content"].lower()
    assert messages[1]["content"] == "How many survivors?"


def test_build_task_brief_scopes_the_role():
    messages = MOD.build_task_brief("tactical", "What is in the approach path?")
    assert "Tactical" in messages[0]["content"] or "tactical" in messages[0]["content"].lower()
    # The subagent must not be handed the lead's conversation.
    assert len(messages) == 2


# --- run_subagent ---


def test_run_subagent_returns_structured_finding():
    client = _subagent_client(_report(claim="Ring holds 8 hours.", window_hours=8.0))
    finding = asyncio.run(MOD.run_subagent(MOD.Brief("logistics", "How long?"), client))

    assert finding.department == "logistics"
    assert finding.report.claim == "Ring holds 8 hours."
    assert finding.report.window_hours == 8.0
    assert client.responses.parse.await_count == 1


def test_run_subagent_passes_the_archive_tool_and_schema():
    client = _subagent_client()
    asyncio.run(MOD.run_subagent(MOD.Brief("medical", "Survivors?"), client))

    kwargs = client.responses.parse.await_args.kwargs
    assert {t["name"] for t in kwargs["tools"]} == {"read_archive"}
    assert kwargs["text_format"] is MOD.SubagentReport


def test_run_subagent_runs_its_tool_then_reports():
    calls = {"n": 0}

    async def parse(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _parsed_response(
                None, [_tool_call("tc1", "read_archive", json.dumps({"query": "docking ring"}))]
            )
        return _parsed_response(_report(claim="Ring holds 8 hours."))

    client = MagicMock()
    client.responses.parse = AsyncMock(side_effect=parse)

    finding = asyncio.run(MOD.run_subagent(MOD.Brief("logistics", "How long?"), client))
    assert finding.report.claim == "Ring holds 8 hours."
    assert client.responses.parse.await_count == 2
    # The archive read stayed inside the subagent and never reached the lead.
    assert finding.raw_chars > len("How long?")


# --- fan_out ---


def test_fan_out_returns_one_finding_per_brief():
    client = _subagent_client()
    briefs = [MOD.Brief(dept, f"{dept} brief") for dept in MOD.DEPARTMENTS]
    findings = asyncio.run(MOD.fan_out(briefs, client, max_workers=3))

    assert len(findings) == len(briefs)
    assert [f.department for f in findings] == [b.department for b in briefs]


def test_fan_out_survives_one_failing_subagent():
    seen = {"n": 0}

    async def parse(**kwargs):
        seen["n"] += 1
        if seen["n"] == 2:
            raise RuntimeError("subagent exploded")
        return _parsed_response(_report())

    client = MagicMock()
    client.responses.parse = AsyncMock(side_effect=parse)

    briefs = [MOD.Brief(dept, f"{dept} brief") for dept in MOD.DEPARTMENTS]
    findings = asyncio.run(MOD.fan_out(briefs, client, max_workers=1))

    assert len(findings) == 3
    assert [f.department for f in findings] == [b.department for b in briefs]
    assert any("fail" in f.report.claim.lower() for f in findings)


def test_fan_out_caps_concurrency_at_max_workers():
    state = {"live": 0, "peak": 0}

    async def parse(**kwargs):
        state["live"] += 1
        state["peak"] = max(state["peak"], state["live"])
        await asyncio.sleep(0.02)
        state["live"] -= 1
        return _parsed_response(_report())

    client = MagicMock()
    client.responses.parse = AsyncMock(side_effect=parse)

    briefs = [MOD.Brief("medical", f"brief {i}") for i in range(6)]
    findings = asyncio.run(MOD.fan_out(briefs, client, max_workers=2))

    assert len(findings) == 6
    assert state["peak"] <= 2


def test_fan_out_runs_briefs_concurrently():
    async def parse(**kwargs):
        await asyncio.sleep(0.05)
        return _parsed_response(_report())

    client = MagicMock()
    client.responses.parse = AsyncMock(side_effect=parse)

    async def timed():
        briefs = [MOD.Brief("medical", f"brief {i}") for i in range(4)]
        loop = asyncio.get_running_loop()
        start = loop.time()
        await MOD.fan_out(briefs, client, max_workers=4)
        return loop.time() - start

    # Four 0.05s subagents serially would be 0.2s.
    assert asyncio.run(timed()) < 0.15


# --- handle_spawn_calls ---


def _spawn_call(call_id, briefs):
    return _tool_call(
        call_id,
        "spawn_researchers",
        json.dumps({"briefs": [{"department": dept, "task": task} for dept, task in briefs]}),
    )


def test_handle_spawn_calls_spawns_every_brief_in_the_call():
    client = _subagent_client()
    response = _text_response(
        tool_calls=[_spawn_call("c1", [("medical", "A"), ("tactical", "B"), ("logistics", "C")])]
    )

    new_items, findings = asyncio.run(MOD.handle_spawn_calls(response, client, max_workers=3))

    assert [f.department for f in findings] == ["medical", "tactical", "logistics"]
    assert [item["call_id"] for item in new_items] == ["c1"]
    assert all(item["type"] == "function_call_output" for item in new_items)
    # One output carrying all three reports — and reports only, not transcripts.
    reports = json.loads(new_items[0]["output"])
    assert len(reports) == 3
    assert "claim" in reports[0]


def test_handle_spawn_calls_merges_several_calls_into_one_fan_out():
    client = _subagent_client()
    response = _text_response(
        tool_calls=[
            _spawn_call("c1", [("medical", "A")]),
            _spawn_call("c2", [("tactical", "B"), ("logistics", "C")]),
        ]
    )

    new_items, findings = asyncio.run(MOD.handle_spawn_calls(response, client, max_workers=3))

    assert [f.department for f in findings] == ["medical", "tactical", "logistics"]
    assert [item["call_id"] for item in new_items] == ["c1", "c2"]
    # Each call_id gets back exactly the reports it asked for.
    assert len(json.loads(new_items[0]["output"])) == 1
    assert len(json.loads(new_items[1]["output"])) == 2


def test_handle_spawn_calls_empty_without_spawn_calls():
    client = _subagent_client()
    new_items, findings = asyncio.run(
        MOD.handle_spawn_calls(_text_response(content="Answer."), client)
    )
    assert new_items == []
    assert findings == []


def test_handle_spawn_calls_rejects_an_invented_department():
    client = _subagent_client()
    response = _text_response(tool_calls=[_spawn_call("c1", [("warp", "A")])])
    _, findings = asyncio.run(MOD.handle_spawn_calls(response, client))
    assert findings[0].department in MOD.DEPARTMENTS


# --- reconcile ---


def test_reconcile_flags_conflicting_numbers():
    findings = [
        _finding("logistics", claim="Ring holds 8 hours.", window_hours=8.0),
        _finding("tactical", claim="Debris blocks in 3 hours.", window_hours=3.0),
    ]
    reconciled = MOD.reconcile(findings)

    assert len(reconciled.conflicts) >= 1
    conflict = " ".join(reconciled.conflicts)
    assert "logistics" in conflict and "tactical" in conflict
    assert len(reconciled.findings) == 2


def test_reconcile_stays_quiet_when_reports_agree():
    findings = [
        _finding("logistics", claim="Ring holds 8 hours.", window_hours=8.0),
        _finding("tactical", claim="Path is clear for 8 hours.", window_hours=8.0),
    ]
    assert MOD.reconcile(findings).conflicts == []


def test_reconcile_flags_low_confidence():
    findings = [_finding("medical", claim="Unclear.", window_hours=None, confidence=0.2)]
    conflicts = " ".join(MOD.reconcile(findings).conflicts)
    assert "medical" in conflicts


def test_reconcile_drops_duplicate_claims():
    findings = [
        _finding("logistics", claim="Ring holds 8 hours.", window_hours=8.0),
        _finding("tactical", claim="Ring holds 8 hours!", window_hours=8.0),
    ]
    reconciled = MOD.reconcile(findings)

    assert len(reconciled.findings) == 1
    assert len(reconciled.duplicates) == 1


# --- synthesise ---


def test_synthesise_passes_every_finding_and_conflict_to_the_merger():
    client = MagicMock()
    client.responses.create = AsyncMock(return_value=_text_response(content="Go in 2 hours."))

    reconciled = MOD.Reconciled(
        findings=[
            _finding("logistics", claim="Ring holds 8 hours.", window_hours=8.0),
            _finding("tactical", claim="Debris blocks in 3 hours.", window_hours=3.0),
        ],
        conflicts=["window closes 5h apart (logistics 8h, tactical 3h)"],
    )
    answer = asyncio.run(MOD.synthesise("Commit to the rescue?", reconciled, client))

    assert answer == "Go in 2 hours."
    sent = json.dumps(client.responses.create.await_args.kwargs["input"])
    assert "Ring holds 8 hours." in sent
    assert "Debris blocks in 3 hours." in sent
    assert "5h apart" in sent


# --- lead_loop ---


def test_lead_loop_spawns_then_merges():
    turns = {"n": 0}

    async def create(**kwargs):
        turns["n"] += 1
        if turns["n"] == 1:
            return _text_response(
                tool_calls=[
                    _spawn_call(
                        "c1",
                        [
                            ("logistics", "How long?"),
                            ("tactical", "What is in the path?"),
                        ],
                    )
                ]
            )
        return _text_response(content="Merged answer.")

    client = MagicMock()
    client.responses.create = AsyncMock(side_effect=create)
    client.responses.parse = AsyncMock(
        side_effect=[
            _parsed_response(_report(claim="Ring holds 8 hours.", window_hours=8.0)),
            _parsed_response(_report(claim="Debris blocks in 3 hours.", window_hours=3.0)),
        ]
    )

    result = asyncio.run(MOD.lead_loop("Commit to the rescue?", client, max_workers=2))

    assert [f.department for f in result["findings"]] == ["logistics", "tactical"]
    assert result["conflicts"], "a 5-hour disagreement should be flagged"
    assert result["answer"]
    assert result["trace"]


def test_lead_loop_answers_directly_without_spawning():
    client = MagicMock()
    client.responses.create = AsyncMock(return_value=_text_response(content="No research needed."))
    client.responses.parse = AsyncMock(return_value=_parsed_response(_report()))

    result = asyncio.run(MOD.lead_loop("What is your name?", client))

    assert result["answer"] == "No research needed."
    assert result["findings"] == []
    assert client.responses.parse.await_count == 0
