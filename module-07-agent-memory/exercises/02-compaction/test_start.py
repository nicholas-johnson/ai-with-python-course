"""Tests for Exercise 02 — Compaction.

No API key needed: the summariser is driven by a fake responses.parse that
returns a canned Compaction.
"""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
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


def _fake_client(mod):
    """A client whose responses.parse returns a fixed Compaction."""
    compaction = mod.Compaction(
        summary="Zara ordered a round for the Pathfinder crew.",
        anchors=[
            mod.Anchor(kind="decision", text="Charge the evening to the ship's account"),
            mod.Anchor(kind="open_task", text="Clear Marek's 12 credits"),
            mod.Anchor(kind="constraint", text="No synthcitrus for Tanaka"),
        ],
    )
    client = MagicMock()
    client.responses.parse.return_value = MagicMock(output_parsed=compaction)
    return client, compaction


TOOL_CALL = {
    "type": "function_call",
    "name": "check_stock",
    "call_id": "call_1",
    "arguments": '{"drink": "Comet Tail"}',
}
TOOL_OUTPUT = {
    "type": "function_call_output",
    "call_id": "call_1",
    "output": '{"units_remaining": 11}',
}


def test_count_tokens_counts_chat_messages():
    """More text means more tokens, and an empty list is free."""
    mod = _import_start()
    assert mod.count_tokens([]) == 0

    short = mod.count_tokens([{"role": "user", "content": "Evening."}])
    long = mod.count_tokens([{"role": "user", "content": "Evening. " * 50}])
    assert 0 < short < long


def test_count_tokens_counts_tool_items():
    """A tool call and its output are not free."""
    mod = _import_start()
    assert mod.count_tokens([TOOL_CALL]) > mod.MESSAGE_OVERHEAD
    assert mod.count_tokens([TOOL_OUTPUT]) > mod.MESSAGE_OVERHEAD


def test_safe_split_leaves_a_clean_boundary_alone():
    """A boundary between ordinary messages does not move."""
    mod = _import_start()
    messages = [{"role": "user", "content": str(i)} for i in range(5)]
    assert mod.safe_split(messages, 3) == 3


def test_safe_split_moves_off_a_tool_output():
    """The boundary moves back so a call and its output stay together."""
    mod = _import_start()
    messages = [
        {"role": "user", "content": "How much is left?"},
        TOOL_CALL,
        TOOL_OUTPUT,
        {"role": "assistant", "content": "Eleven units."},
    ]
    assert mod.safe_split(messages, 2) == 1, "Index 2 is the output — move back to its call"


def test_safe_split_clamps_out_of_range():
    mod = _import_start()
    messages = [{"role": "user", "content": "one"}]
    assert mod.safe_split(messages, 99) == 1
    assert mod.safe_split(messages, -5) == 0


def test_render_block_lists_anchors_by_kind():
    """The block carries the summary and labels every kind present."""
    mod = _import_start()
    _, compaction = _fake_client(mod)

    block = mod.render_block(compaction)
    assert "[Earlier conversation]" in block
    assert "Zara ordered a round" in block
    assert "Decisions: Charge the evening to the ship's account" in block
    assert "Open tasks: Clear Marek's 12 credits" in block
    assert "Constraints: No synthcitrus for Tanaka" in block


def test_render_block_reemits_carried_anchors():
    """Anchors from an earlier pass survive the next one verbatim."""
    mod = _import_start()
    _, compaction = _fake_client(mod)
    carried = [mod.Anchor(kind="decision", text="Zara has standing authority")]

    block = mod.render_block(compaction, carried)
    assert "Zara has standing authority" in block
    assert "Charge the evening to the ship's account" in block


def test_render_block_omits_empty_kinds():
    mod = _import_start()
    compaction = mod.Compaction(
        summary="Quiet evening.",
        anchors=[mod.Anchor(kind="decision", text="Close at 0200")],
    )
    block = mod.render_block(compaction)
    assert "Decisions:" in block
    assert "Open tasks:" not in block
    assert "Constraints:" not in block


def test_compact_is_a_no_op_under_budget():
    """No model call happens while the thread still fits."""
    mod = _import_start()
    client, _ = _fake_client(mod)
    thread = [{"role": "user", "content": "Evening."}]

    result, report = mod.compact(thread, budget_tokens=10_000, keep_recent=4, client=client)
    assert report is None
    assert result == thread
    client.responses.parse.assert_not_called()


def test_compact_replaces_the_old_span_with_one_block():
    """Over budget, the old span becomes a single system message."""
    mod = _import_start()
    client, _ = _fake_client(mod)
    thread = [{"role": "user", "content": f"Turn number {i} of the evening."} for i in range(12)]

    result, report = mod.compact(thread, budget_tokens=20, keep_recent=4, client=client)

    assert report is not None
    assert result[0]["role"] == "system"
    assert "[Earlier conversation]" in result[0]["content"]
    assert result[1:] == thread[-4:], "The recent messages stay verbatim"
    assert report.messages_compacted == 8
    assert report.tokens_after < report.tokens_before


def test_compact_keeps_tool_pairs_together():
    """The split boundary moves rather than orphaning a tool output."""
    mod = _import_start()
    client, _ = _fake_client(mod)
    thread = [{"role": "user", "content": f"Turn {i} of a long evening."} for i in range(8)]
    thread += [TOOL_CALL, TOOL_OUTPUT, {"role": "assistant", "content": "Eleven units."}]

    result, report = mod.compact(thread, budget_tokens=20, keep_recent=2, client=client)

    assert report.actual_split != report.requested_split, "The boundary should have moved"
    kept = [m.get("type") for m in result[1:]]
    assert kept.count("function_call") == kept.count("function_call_output") == 1


def test_compact_report_counts_tokens():
    mod = _import_start()
    client, _ = _fake_client(mod)
    thread = [{"role": "user", "content": f"Turn number {i} of the evening."} for i in range(12)]

    _, report = mod.compact(thread, budget_tokens=20, keep_recent=4, client=client)
    assert report.tokens_before == mod.count_tokens(thread)
    assert report.tokens_after > 0


def test_build_system_prompt_includes_memories():
    mod = _import_start()
    memory = MagicMock(text="Zara takes the Comet Tail with extra fizz.")

    assert "Comet Tail" in mod.build_system_prompt([memory])
    assert "BARKEEP" in mod.build_system_prompt([])
    assert "Comet Tail" not in mod.build_system_prompt([])


def test_sample_thread_contains_a_tool_pair():
    """The /seed thread has to exercise the tool-pair path."""
    mod = _import_start()
    types = [m.get("type") for m in mod.SAMPLE_THREAD]
    assert "function_call" in types
    assert "function_call_output" in types


@pytest.mark.parametrize("budget", [0, 20])
def test_compact_handles_short_threads(budget):
    """A thread no longer than keep_recent is left alone."""
    mod = _import_start()
    client, _ = _fake_client(mod)
    thread = [{"role": "user", "content": "Evening."}, {"role": "assistant", "content": "Hello."}]

    result, report = mod.compact(thread, budget_tokens=budget, keep_recent=4, client=client)
    assert report is None
    assert result == thread
