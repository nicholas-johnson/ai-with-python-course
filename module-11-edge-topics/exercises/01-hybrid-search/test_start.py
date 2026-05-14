"""Tests for Exercise 01 — Hybrid Search."""

import math
from start import bm25_search, reciprocal_rank_fusion, vector_search, hybrid_search


DOCUMENTS = [
    {"id": "doc1", "text": "The reactor core temperature is rising rapidly"},
    {"id": "doc2", "text": "Hull integrity on deck 5 shows minor damage"},
    {"id": "doc3", "text": "Navigation systems are operating normally"},
    {"id": "doc4", "text": "The reactor cooling system needs maintenance"},
    {"id": "doc5", "text": "Emergency protocols for hull breach on deck 7"},
]

EMBEDDINGS = {
    "doc1": [0.9, 0.1, 0.0, 0.0],
    "doc2": [0.0, 0.8, 0.2, 0.0],
    "doc3": [0.0, 0.0, 0.9, 0.1],
    "doc4": [0.8, 0.2, 0.0, 0.0],
    "doc5": [0.1, 0.7, 0.1, 0.1],
}


class TestBM25Search:
    def test_returns_list_of_ids(self):
        results = bm25_search("reactor temperature", DOCUMENTS)
        assert isinstance(results, list)
        assert all(isinstance(r, str) for r in results)

    def test_relevant_docs_ranked_higher(self):
        results = bm25_search("reactor", DOCUMENTS)
        assert "doc1" in results[:3]
        assert "doc4" in results[:3]

    def test_respects_top_k(self):
        results = bm25_search("reactor", DOCUMENTS, top_k=2)
        assert len(results) <= 2

    def test_all_docs_returned_by_default(self):
        results = bm25_search("the", DOCUMENTS)
        assert len(results) <= len(DOCUMENTS)


class TestReciprocalRankFusion:
    def test_basic_fusion(self):
        list1 = ["a", "b", "c"]
        list2 = ["b", "a", "d"]
        results = reciprocal_rank_fusion([list1, list2], k=60)
        assert isinstance(results, list)
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_doc_in_both_lists_scores_higher(self):
        list1 = ["a", "b", "c"]
        list2 = ["b", "c", "d"]
        results = reciprocal_rank_fusion([list1, list2], k=60)
        scores = dict(results)
        assert scores["b"] > scores["a"]
        assert scores["b"] > scores["d"]

    def test_single_list(self):
        results = reciprocal_rank_fusion([["x", "y", "z"]], k=60)
        scores = dict(results)
        assert scores["x"] > scores["y"] > scores["z"]

    def test_rrf_score_formula(self):
        results = reciprocal_rank_fusion([["a", "b"], ["a", "c"]], k=60)
        scores = dict(results)
        expected_a = 1 / (60 + 1) + 1 / (60 + 1)
        assert abs(scores["a"] - expected_a) < 1e-9

    def test_empty_lists(self):
        results = reciprocal_rank_fusion([[], []], k=60)
        assert results == []


class TestVectorSearch:
    def test_returns_ranked_ids(self):
        query_emb = [0.9, 0.1, 0.0, 0.0]
        results = vector_search(query_emb, EMBEDDINGS)
        assert isinstance(results, list)
        assert results[0] == "doc1"

    def test_respects_top_k(self):
        query_emb = [0.5, 0.5, 0.0, 0.0]
        results = vector_search(query_emb, EMBEDDINGS, top_k=2)
        assert len(results) == 2

    def test_different_query_different_ranking(self):
        results1 = vector_search([1.0, 0.0, 0.0, 0.0], EMBEDDINGS)
        results2 = vector_search([0.0, 0.0, 1.0, 0.0], EMBEDDINGS)
        assert results1[0] != results2[0]


class TestHybridSearch:
    def test_returns_fused_results(self):
        query_emb = [0.9, 0.1, 0.0, 0.0]
        results = hybrid_search(
            "reactor temperature", DOCUMENTS, query_emb, EMBEDDINGS,
        )
        assert isinstance(results, list)
        assert len(results) <= 5

    def test_results_are_tuples(self):
        query_emb = [0.9, 0.1, 0.0, 0.0]
        results = hybrid_search(
            "reactor temperature", DOCUMENTS, query_emb, EMBEDDINGS,
        )
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], float)

    def test_top_result_is_relevant(self):
        query_emb = [0.9, 0.1, 0.0, 0.0]
        results = hybrid_search(
            "reactor", DOCUMENTS, query_emb, EMBEDDINGS,
        )
        top_ids = [r[0] for r in results[:2]]
        assert "doc1" in top_ids or "doc4" in top_ids
