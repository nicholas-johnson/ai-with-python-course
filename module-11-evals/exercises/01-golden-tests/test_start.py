"""Tests for Exercise 01 — Golden Tests."""

import json
from unittest.mock import MagicMock

from start import load_build, load_cases, make_scripted_client, run_case, run_suite, score_case


def _tool_message(name: str, arguments: dict, call_id: str = "call_1"):
    """A mock response whose output is one function_call item."""
    tc = MagicMock(type="function_call", call_id=call_id, arguments=json.dumps(arguments))
    tc.name = name  # MagicMock(name=...) would name the mock, not set .name
    return MagicMock(output=[tc], output_text="")


def _content_message(text: str):
    """A mock response with a final text answer."""
    return MagicMock(output=[], output_text=text)


CASE_ENG = {
    "id": "crew-count-engineering",
    "question": "How many people are in engineering?",
    "expected_tools": [
        {"name": "get_crew_count", "arguments": {"department": "engineering"}}
    ],
    "expected_answer": "Engineering has 2 crew members.",
}

CASE_DIRECT = {
    "id": "direct-answer",
    "question": "What ship are we on?",
    "expected_tools": [],
    "expected_answer": "You are aboard the DSS Pathfinder.",
}


class TestRunCase:
    def test_records_tool_and_answer(self):
        client = MagicMock()
        client.responses.create.side_effect = [
            _tool_message("get_crew_count", {"department": "engineering"}),
            _content_message("Engineering has 2 crew members."),
        ]
        result = run_case(client, CASE_ENG)
        assert result["tools"] == CASE_ENG["expected_tools"]
        assert result["answer"] == CASE_ENG["expected_answer"]

    def test_direct_answer_no_tools(self):
        client = MagicMock()
        client.responses.create.return_value = _content_message(
            "You are aboard the DSS Pathfinder."
        )
        result = run_case(client, CASE_DIRECT)
        assert result["tools"] == []
        assert result["answer"] == CASE_DIRECT["expected_answer"]

    def test_calls_openai(self):
        client = MagicMock()
        client.responses.create.return_value = _content_message("ok")
        run_case(client, CASE_DIRECT)
        client.responses.create.assert_called()

    def test_scripted_build_drives_loop(self):
        build = {
            "Warp status?": [
                {
                    "tool_calls": [
                        {
                            "id": "c1",
                            "name": "get_ship_status",
                            "arguments": {"system": "warp"},
                        }
                    ]
                },
                {"content": "Warp is online at 97% efficiency."},
            ]
        }
        case = {
            "id": "warp",
            "question": "Warp status?",
            "expected_tools": [
                {"name": "get_ship_status", "arguments": {"system": "warp"}}
            ],
            "expected_answer": "Warp is online at 97% efficiency.",
        }
        result = run_case(make_scripted_client(build), case)
        assert result["tools"] == case["expected_tools"]
        assert result["answer"] == case["expected_answer"]


class TestScoreCase:
    def test_pass_when_exact_match(self):
        result = {
            "tools": CASE_ENG["expected_tools"],
            "answer": CASE_ENG["expected_answer"],
        }
        scored = score_case(result, CASE_ENG)
        assert scored["passed"] is True
        assert scored["mismatches"] == []
        assert scored["id"] == CASE_ENG["id"]

    def test_tools_mismatch(self):
        result = {
            "tools": [{"name": "search_crew", "arguments": {"query": "Voss"}}],
            "answer": CASE_ENG["expected_answer"],
        }
        scored = score_case(result, CASE_ENG)
        assert scored["passed"] is False
        assert "tools" in scored["mismatches"]

    def test_answer_mismatch(self):
        result = {
            "tools": CASE_ENG["expected_tools"],
            "answer": "wrong",
        }
        scored = score_case(result, CASE_ENG)
        assert scored["passed"] is False
        assert "answer" in scored["mismatches"]

    def test_both_mismatch(self):
        result = {"tools": [], "answer": "nope"}
        scored = score_case(result, CASE_ENG)
        assert set(scored["mismatches"]) == {"tools", "answer"}


class TestRunSuite:
    def test_counts_pass_and_fail(self):
        client = MagicMock()
        client.responses.create.return_value = _content_message(
            "You are aboard the DSS Pathfinder."
        )
        summary = run_suite(client, [CASE_DIRECT, CASE_ENG])
        assert summary["total"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert len(summary["results"]) == 2

    def test_empty_suite(self):
        client = MagicMock()
        summary = run_suite(client, [])
        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["results"] == []


class TestShippedBuilds:
    """The point of the lab: one reference, two builds, different verdicts."""

    def test_build_a_passes_every_case(self):
        cases = load_cases()
        summary = run_suite(make_scripted_client(load_build("build-a")), cases)
        assert summary["passed"] == summary["total"]
        assert summary["failed"] == 0

    def test_build_b_fails(self):
        cases = load_cases()
        summary = run_suite(make_scripted_client(load_build("build-b")), cases)
        assert summary["failed"] > 0

    def test_build_b_dropped_a_tool_call(self):
        cases = load_cases()
        summary = run_suite(make_scripted_client(load_build("build-b")), cases)
        warp = next(r for r in summary["results"] if r["id"] == "ship-status-warp")
        assert "tools" in warp["mismatches"]

    def test_build_b_paraphrase_is_an_answer_only_mismatch(self):
        # Right facts, different words. Exact match cannot tell this from a
        # real regression — that is what the judge in exercise 03 is for.
        cases = load_cases()
        summary = run_suite(make_scripted_client(load_build("build-b")), cases)
        captain = next(r for r in summary["results"] if r["id"] == "search-captain")
        assert captain["mismatches"] == ["answer"]


class TestGoldenFile:
    def test_holds_only_the_reference(self):
        # If the golden file also scripted the agent, the suite would be
        # comparing the script to itself and would pass forever.
        for case in load_cases():
            assert set(case) == {"id", "question", "expected_tools", "expected_answer"}
