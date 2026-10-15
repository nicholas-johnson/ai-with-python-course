"""Tests for Exercise 05 — Eval Compare."""

import pytest
from start import (
    build_scorecard,
    compare_configs,
    gate,
    metric_value,
    overall_score,
)

RETRIEVAL = {"avg_recall": 0.8, "avg_precision": 0.6, "avg_mrr": 0.85}
JUDGE = {"avg_correctness": 4.0, "avg_completeness": 4.0, "avg_relevance": 4.0}
FAITH = {"avg_faithfulness": 0.9}

# 0.35*0.8 + 0.35*(12/15) + 0.30*0.9 = 0.28 + 0.28 + 0.27 = 0.83
EXPECTED_OVERALL = pytest.approx(0.83)


class TestOverallScore:
    def test_formula(self):
        assert overall_score(RETRIEVAL, JUDGE, FAITH) == EXPECTED_OVERALL

    def test_perfect(self):
        retrieval = {"avg_recall": 1.0, "avg_precision": 1.0, "avg_mrr": 1.0}
        judge = {"avg_correctness": 5.0, "avg_completeness": 5.0, "avg_relevance": 5.0}
        faith = {"avg_faithfulness": 1.0}
        assert overall_score(retrieval, judge, faith) == pytest.approx(1.0)


class TestBuildScorecard:
    def test_shape(self):
        card = build_scorecard("rag_rerank", RETRIEVAL, JUDGE, FAITH)
        assert card["config"] == "rag_rerank"
        assert card["retrieval"] == RETRIEVAL
        assert card["judge"] == JUDGE
        assert card["faithfulness"] == FAITH
        assert card["overall"] == EXPECTED_OVERALL


class TestMetricValue:
    def test_overall(self):
        card = build_scorecard("x", RETRIEVAL, JUDGE, FAITH)
        assert metric_value(card, "overall") == EXPECTED_OVERALL

    def test_nested(self):
        card = build_scorecard("x", RETRIEVAL, JUDGE, FAITH)
        assert metric_value(card, "avg_recall") == 0.8
        assert metric_value(card, "avg_correctness") == 4.0
        assert metric_value(card, "avg_faithfulness") == 0.9


class TestCompareConfigs:
    def test_winner_overall(self):
        low = build_scorecard(
            "rag",
            {"avg_recall": 0.4, "avg_precision": 0.3, "avg_mrr": 0.3},
            {"avg_correctness": 2.0, "avg_completeness": 2.0, "avg_relevance": 2.0},
            {"avg_faithfulness": 0.4},
        )
        high = build_scorecard("rag_rerank", RETRIEVAL, JUDGE, FAITH)
        result = compare_configs([low, high], metric="overall")
        assert result["winner"] == "rag_rerank"
        assert result["metric"] == "overall"
        assert result["ranking"][0]["config"] == "rag_rerank"
        assert result["ranking"][1]["config"] == "rag"

    def test_winner_by_recall(self):
        a = build_scorecard(
            "a",
            {"avg_recall": 0.9, "avg_precision": 0.1, "avg_mrr": 0.1},
            JUDGE,
            FAITH,
        )
        b = build_scorecard(
            "b",
            {"avg_recall": 0.2, "avg_precision": 0.9, "avg_mrr": 0.9},
            JUDGE,
            FAITH,
        )
        result = compare_configs([a, b], metric="avg_recall")
        assert result["winner"] == "a"

    def test_empty(self):
        result = compare_configs([], metric="overall")
        assert result["winner"] is None
        assert result["ranking"] == []


class TestGate:
    def test_passes_when_above_floors(self):
        card = build_scorecard("rag_rerank", RETRIEVAL, JUDGE, FAITH)
        result = gate(card, {"avg_recall": 0.6, "overall": 0.5})
        assert result["passed"] is True
        assert result["failures"] == []

    def test_fails_below_floor(self):
        card = build_scorecard(
            "rag",
            {"avg_recall": 0.4, "avg_precision": 0.3, "avg_mrr": 0.3},
            {"avg_correctness": 2.0, "avg_completeness": 2.0, "avg_relevance": 2.0},
            {"avg_faithfulness": 0.4},
        )
        result = gate(card, {"avg_recall": 0.6, "avg_faithfulness": 0.75})
        assert result["passed"] is False
        metrics = {f["metric"] for f in result["failures"]}
        assert metrics == {"avg_recall", "avg_faithfulness"}
        recall_fail = next(f for f in result["failures"] if f["metric"] == "avg_recall")
        assert recall_fail["value"] == 0.4
        assert recall_fail["threshold"] == 0.6

    def test_equal_to_threshold_passes(self):
        card = build_scorecard("x", RETRIEVAL, JUDGE, FAITH)
        result = gate(card, {"avg_recall": 0.8})
        assert result["passed"] is True
