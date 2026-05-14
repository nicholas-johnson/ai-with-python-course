"""Tests for Exercise 08 — LLM Eval."""

import json
from unittest.mock import MagicMock
from start import llm_judge, evaluate_dataset, compute_summary


def make_mock_client(judge_response=None):
    if judge_response is None:
        judge_response = {
            "correctness": 4,
            "completeness": 3,
            "relevance": 5,
            "explanation": "Good answer overall.",
        }
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = json.dumps(judge_response)
    client.chat.completions.create.return_value = response
    return client


TEST_CASES = [
    {
        "question": "What is the reactor temperature?",
        "answer": "The reactor runs at 5000K.",
        "reference": "The reactor core operates at approximately 5000 degrees Kelvin.",
    },
    {
        "question": "How many decks does the ship have?",
        "answer": "The ship has 7 decks.",
        "reference": "The vessel has 7 main decks and 2 sub-decks.",
    },
]


class TestLLMJudge:
    def test_returns_dict(self):
        client = make_mock_client()
        result = llm_judge(client, "question", "answer", "reference")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        client = make_mock_client()
        result = llm_judge(client, "q", "a", "r")
        assert "correctness" in result
        assert "completeness" in result
        assert "relevance" in result
        assert "explanation" in result

    def test_scores_are_integers(self):
        client = make_mock_client()
        result = llm_judge(client, "q", "a", "r")
        assert isinstance(result["correctness"], int)
        assert isinstance(result["completeness"], int)
        assert isinstance(result["relevance"], int)

    def test_calls_openai(self):
        client = make_mock_client()
        llm_judge(client, "q", "a", "r")
        client.chat.completions.create.assert_called_once()


class TestEvaluateDataset:
    def test_returns_list(self):
        client = make_mock_client()
        results = evaluate_dataset(client, TEST_CASES)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_results_contain_scores(self):
        client = make_mock_client()
        results = evaluate_dataset(client, TEST_CASES)
        for r in results:
            assert "correctness" in r
            assert "completeness" in r
            assert "relevance" in r

    def test_results_contain_original_data(self):
        client = make_mock_client()
        results = evaluate_dataset(client, TEST_CASES)
        assert results[0]["question"] == TEST_CASES[0]["question"]
        assert results[0]["answer"] == TEST_CASES[0]["answer"]

    def test_empty_dataset(self):
        client = make_mock_client()
        results = evaluate_dataset(client, [])
        assert results == []


class TestComputeSummary:
    def test_returns_averages(self):
        results = [
            {"correctness": 4, "completeness": 3, "relevance": 5},
            {"correctness": 2, "completeness": 5, "relevance": 3},
        ]
        summary = compute_summary(results)
        assert summary["avg_correctness"] == 3.0
        assert summary["avg_completeness"] == 4.0
        assert summary["avg_relevance"] == 4.0
        assert summary["num_cases"] == 2

    def test_single_result(self):
        results = [{"correctness": 5, "completeness": 4, "relevance": 3}]
        summary = compute_summary(results)
        assert summary["avg_correctness"] == 5.0
        assert summary["num_cases"] == 1

    def test_empty_results(self):
        summary = compute_summary([])
        assert summary["num_cases"] == 0
        assert summary["avg_correctness"] == 0.0

    def test_returns_float_averages(self):
        results = [
            {"correctness": 3, "completeness": 4, "relevance": 5},
            {"correctness": 4, "completeness": 3, "relevance": 4},
        ]
        summary = compute_summary(results)
        assert isinstance(summary["avg_correctness"], float)
        assert isinstance(summary["avg_completeness"], float)
