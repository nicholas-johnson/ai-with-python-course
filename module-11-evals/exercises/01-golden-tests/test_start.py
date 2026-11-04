"""Tests for Exercise 01 — Golden Tests."""

import json
from unittest.mock import MagicMock

import pytest

from start import (
    PASS_THRESHOLD,
    load_build,
    load_cases,
    make_canned_judge,
    make_scripted_client,
    normalise,
    run_case,
    run_suite,
    score_case,
)


def _judge(correctness=5, completeness=5, relevance=5):
    """A judge stub that always returns the same verdict."""

    def judge(case_id, question, answer, reference):
        return {
            "correctness": correctness,
            "completeness": completeness,
            "relevance": relevance,
            "explanation": "stub",
        }

    return judge


def _exact_judge(case_id, question, answer, reference):
    """A judge stub that is generous on an exact answer and harsh otherwise."""
    score = 5 if answer == reference else 1
    return {
        "correctness": score,
        "completeness": score,
        "relevance": score,
        "explanation": "stub",
    }


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


class TestNormalise:
    def test_maps_the_rubric_onto_zero_one(self):
        assert normalise(1) == 0.0
        assert normalise(3) == 0.5
        assert normalise(5) == 1.0


class TestScoreCase:
    def test_perfect_case_scores_one(self):
        result = {
            "tools": CASE_ENG["expected_tools"],
            "answer": CASE_ENG["expected_answer"],
        }
        scored = score_case(result, CASE_ENG, _judge())
        assert scored["score"] == 1.0
        assert scored["passed"] is True
        assert scored["id"] == CASE_ENG["id"]

    def test_criteria_are_all_in_range(self):
        result = {"tools": [], "answer": "nope"}
        scored = score_case(result, CASE_ENG, _judge(2, 3, 4))
        assert set(scored["criteria"]) == {
            "tools",
            "correctness",
            "completeness",
            "relevance",
        }
        assert all(0.0 <= value <= 1.0 for value in scored["criteria"].values())
        assert 0.0 <= scored["score"] <= 1.0

    def test_score_is_the_mean_of_the_criteria(self):
        result = {
            "tools": CASE_ENG["expected_tools"],
            "answer": CASE_ENG["expected_answer"],
        }
        scored = score_case(result, CASE_ENG, _judge(5, 1, 3))
        # tools 1.0, correctness 1.0, completeness 0.0, relevance 0.5
        assert scored["score"] == pytest.approx(0.625)

    def test_wrong_tools_cost_a_whole_criterion(self):
        result = {
            "tools": [{"name": "search_crew", "arguments": {"query": "Voss"}}],
            "answer": CASE_ENG["expected_answer"],
        }
        scored = score_case(result, CASE_ENG, _judge())
        assert scored["criteria"]["tools"] == 0.0
        assert scored["score"] == pytest.approx(0.75)
        assert scored["passed"] is False

    def test_paraphrase_still_passes(self):
        # The whole reason prose is judged rather than string-compared.
        result = {
            "tools": CASE_ENG["expected_tools"],
            "answer": "There are 2 crew in engineering.",
        }
        scored = score_case(result, CASE_ENG, _judge(5, 5, 5))
        assert scored["score"] == 1.0
        assert scored["passed"] is True

    def test_judge_explanation_is_carried_through(self):
        result = {"tools": [], "answer": "nope"}
        scored = score_case(result, CASE_ENG, _judge(1, 1, 1))
        assert scored["explanation"] == "stub"


class TestRunSuite:
    def test_counts_pass_and_fail(self):
        client = MagicMock()
        client.responses.create.return_value = _content_message(
            "You are aboard the DSS Pathfinder."
        )
        summary = run_suite(client, [CASE_DIRECT, CASE_ENG], _exact_judge)
        assert summary["total"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert len(summary["results"]) == 2

    def test_suite_is_the_mean_of_the_case_scores(self):
        client = MagicMock()
        client.responses.create.return_value = _content_message(
            "You are aboard the DSS Pathfinder."
        )
        summary = run_suite(client, [CASE_DIRECT, CASE_ENG], _exact_judge)
        scores = [r["score"] for r in summary["results"]]
        assert summary["suite"] == pytest.approx(sum(scores) / len(scores))

    def test_empty_suite(self):
        client = MagicMock()
        summary = run_suite(client, [], _judge())
        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["suite"] == 0.0
        assert summary["results"] == []


class TestShippedBuilds:
    """The point of the lab: one reference, two builds, different verdicts."""

    def _run(self, build_name):
        return run_suite(
            make_scripted_client(load_build(build_name)),
            load_cases(),
            make_canned_judge(build_name),
        )

    def test_build_a_passes_every_case(self):
        summary = self._run("build-a")
        assert summary["passed"] == summary["total"]
        assert summary["failed"] == 0
        assert summary["suite"] == 1.0

    def test_build_b_fails(self):
        summary = self._run("build-b")
        assert summary["failed"] > 0

    def test_build_b_scores_below_build_a(self):
        assert self._run("build-b")["suite"] < self._run("build-a")["suite"]

    def test_build_b_dropped_a_tool_call(self):
        summary = self._run("build-b")
        warp = next(r for r in summary["results"] if r["id"] == "ship-status-warp")
        assert warp["criteria"]["tools"] == 0.0
        assert warp["passed"] is False

    def test_build_b_paraphrase_passes(self):
        # Right facts, reordered clause. A string comparison would call this a
        # regression; the judge scores it full marks and the case passes.
        summary = self._run("build-b")
        captain = next(r for r in summary["results"] if r["id"] == "search-captain")
        assert captain["criteria"]["tools"] == 1.0
        assert captain["score"] >= PASS_THRESHOLD
        assert captain["passed"] is True


class TestGoldenFile:
    def test_holds_only_the_reference(self):
        # If the golden file also scripted the agent, the suite would be
        # comparing the script to itself and would pass forever.
        for case in load_cases():
            assert set(case) == {"id", "question", "expected_tools", "expected_answer"}


class TestCannedJudge:
    def test_covers_every_case_in_both_builds(self):
        cases = load_cases()
        for build_name in ("build-a", "build-b"):
            judge = make_canned_judge(build_name)
            for case in cases:
                verdict = judge(case["id"], case["question"], "x", case["expected_answer"])
                assert set(verdict) >= {
                    "correctness",
                    "completeness",
                    "relevance",
                    "explanation",
                }

    def test_rubric_scores_stay_in_range(self):
        cases = load_cases()
        for build_name in ("build-a", "build-b"):
            judge = make_canned_judge(build_name)
            for case in cases:
                verdict = judge(case["id"], case["question"], "x", case["expected_answer"])
                for name in ("correctness", "completeness", "relevance"):
                    assert 1 <= verdict[name] <= 5
