"""Tests for Exercise 11 — Semantic Caching."""

import math
from unittest.mock import MagicMock
from start import cosine_similarity, SemanticCache


def make_mock_client(embedding=None):
    if embedding is None:
        embedding = [0.1, 0.2, 0.3]
    client = MagicMock()
    response = MagicMock()
    data = MagicMock()
    data.embedding = embedding
    response.data = [data]
    client.embeddings.create.return_value = response
    return client


class TestCosineSimilarity:
    def test_identical_vectors(self):
        a = [1.0, 2.0, 3.0]
        assert abs(cosine_similarity(a, a) - 1.0) < 1e-9

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cosine_similarity(a, b)) < 1e-9

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-9

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 2.0]
        assert cosine_similarity(a, b) == 0.0

    def test_similar_vectors(self):
        a = [1.0, 2.0, 3.0]
        b = [1.1, 2.1, 3.1]
        sim = cosine_similarity(a, b)
        assert sim > 0.99

    def test_returns_float(self):
        result = cosine_similarity([1.0, 0.0], [0.5, 0.5])
        assert isinstance(result, float)


class TestSemanticCacheInit:
    def test_starts_empty(self):
        client = make_mock_client()
        cache = SemanticCache(client, threshold=0.95)
        assert cache.size() == 0

    def test_stores_threshold(self):
        client = make_mock_client()
        cache = SemanticCache(client, threshold=0.9)
        assert cache.threshold == 0.9


class TestSemanticCacheSet:
    def test_adds_entry(self):
        client = make_mock_client([0.1, 0.2, 0.3])
        cache = SemanticCache(client, threshold=0.95)
        cache.set("What is X?", "X is Y.")
        assert cache.size() == 1

    def test_multiple_entries(self):
        client = make_mock_client([0.1, 0.2, 0.3])
        cache = SemanticCache(client, threshold=0.95)
        cache.set("Q1", "A1")
        cache.set("Q2", "A2")
        assert cache.size() == 2

    def test_calls_embedding_api(self):
        client = make_mock_client()
        cache = SemanticCache(client, threshold=0.95)
        cache.set("test query", "test response")
        client.embeddings.create.assert_called_once()


class TestSemanticCacheGet:
    def test_returns_none_for_empty_cache(self):
        client = make_mock_client()
        cache = SemanticCache(client, threshold=0.95)
        result = cache.get("Any query")
        assert result is None

    def test_cache_hit_with_identical_embedding(self):
        embedding = [0.5, 0.5, 0.5]
        client = make_mock_client(embedding)
        cache = SemanticCache(client, threshold=0.95)
        cache.set("What is the capital of France?", "Paris is the capital.")
        result = cache.get("What is France's capital?")
        assert result == "Paris is the capital."

    def test_cache_miss_with_different_embedding(self):
        call_count = [0]
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]

        client = MagicMock()

        def create_embedding(**kwargs):
            idx = min(call_count[0], len(embeddings) - 1)
            call_count[0] += 1
            response = MagicMock()
            data = MagicMock()
            data.embedding = embeddings[idx]
            response.data = [data]
            return response

        client.embeddings.create.side_effect = create_embedding

        cache = SemanticCache(client, threshold=0.95)
        cache.set("About reactors", "Reactor info")
        result = cache.get("About hull integrity")
        assert result is None

    def test_returns_string_on_hit(self):
        embedding = [0.3, 0.3, 0.3]
        client = make_mock_client(embedding)
        cache = SemanticCache(client, threshold=0.9)
        cache.set("test", "cached response")
        result = cache.get("test")
        assert isinstance(result, str)
