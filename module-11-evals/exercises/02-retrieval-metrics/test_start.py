"""Tests for Exercise 02 — Retrieval Metrics."""

from start import evaluate_queries, mrr, precision_at_k, recall_at_k, summarize


class TestRecallAtK:
    def test_all_relevant_in_top_k(self):
        assert recall_at_k(["A", "B", "C"], ["A", "B"], k=3) == 1.0

    def test_partial(self):
        assert recall_at_k(["A", "X", "Y"], ["A", "B"], k=3) == 0.5

    def test_none(self):
        assert recall_at_k(["X", "Y"], ["A"], k=2) == 0.0

    def test_k_cuts_off(self):
        # B is relevant but sits at rank 3; k=2 misses it
        assert recall_at_k(["A", "X", "B"], ["A", "B"], k=2) == 0.5

    def test_empty_relevant(self):
        assert recall_at_k(["A"], [], k=1) == 0.0


class TestPrecisionAtK:
    def test_all_hits(self):
        assert precision_at_k(["A", "B"], ["A", "B", "C"], k=2) == 1.0

    def test_half(self):
        assert precision_at_k(["A", "X", "Y"], ["A"], k=2) == 0.5

    def test_divides_by_k_not_len(self):
        # Only one result returned, k=3 → 1/3 not 1/1
        assert precision_at_k(["A"], ["A"], k=3) == 1 / 3

    def test_k_zero(self):
        assert precision_at_k(["A"], ["A"], k=0) == 0.0


class TestMrr:
    def test_first_rank(self):
        assert mrr(["A", "B"], ["A"]) == 1.0

    def test_second_rank(self):
        assert mrr(["X", "A"], ["A"]) == 0.5

    def test_no_hit(self):
        assert mrr(["X", "Y"], ["A"]) == 0.0

    def test_first_of_several_relevant(self):
        assert mrr(["X", "B", "A"], ["A", "B"]) == 0.5


class TestEvaluateQueries:
    def test_adds_metrics(self):
        queries = [
            {"query": "q1", "ranked_ids": ["A", "B"], "relevant_ids": ["A"]},
        ]
        results = evaluate_queries(queries, k=2)
        assert len(results) == 1
        assert results[0]["recall"] == 1.0
        assert results[0]["precision"] == 0.5
        assert results[0]["mrr"] == 1.0
        assert results[0]["query"] == "q1"

    def test_empty(self):
        assert evaluate_queries([], k=3) == []


class TestSummarize:
    def test_averages(self):
        evaluations = [
            {"recall": 1.0, "precision": 0.5, "mrr": 1.0},
            {"recall": 0.5, "precision": 0.5, "mrr": 0.5},
        ]
        summary = summarize(evaluations)
        assert summary["avg_recall"] == 0.75
        assert summary["avg_precision"] == 0.5
        assert summary["avg_mrr"] == 0.75
        assert summary["num_queries"] == 2

    def test_empty(self):
        summary = summarize([])
        assert summary["num_queries"] == 0
        assert summary["avg_recall"] == 0.0
        assert summary["avg_precision"] == 0.0
        assert summary["avg_mrr"] == 0.0
