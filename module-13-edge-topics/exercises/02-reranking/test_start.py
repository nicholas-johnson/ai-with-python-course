"""Tests for Exercise 02 — Re-ranking."""

from unittest.mock import MagicMock, patch
from start import score_relevance, rerank, two_stage_retrieve


def make_mock_client(score_text="7"):
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = score_text
    client.chat.completions.create.return_value = response
    return client


PASSAGES = [
    {"id": "p1", "text": "The reactor core operates at 5000 degrees Kelvin."},
    {"id": "p2", "text": "Crew rotations happen every 6 months."},
    {"id": "p3", "text": "Reactor maintenance requires full shutdown."},
    {"id": "p4", "text": "The cafeteria menu changes weekly."},
]


class TestScoreRelevance:
    def test_returns_float(self):
        client = make_mock_client("8")
        score = score_relevance(client, "reactor temperature", "The reactor runs hot.")
        assert isinstance(score, float)
        assert score == 8.0

    def test_handles_invalid_response(self):
        client = make_mock_client("not a number")
        score = score_relevance(client, "query", "passage")
        assert isinstance(score, float)
        assert score == 0.0

    def test_calls_openai(self):
        client = make_mock_client("5")
        score_relevance(client, "test query", "test passage")
        client.chat.completions.create.assert_called_once()


class TestRerank:
    def test_returns_sorted_passages(self):
        scores = iter(["3", "9", "6", "1"])
        client = MagicMock()

        def create_response(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = next(scores)
            return resp

        client.chat.completions.create.side_effect = create_response

        results = rerank(client, "reactor", PASSAGES, top_k=2)
        assert len(results) == 2
        assert results[0]["rerank_score"] >= results[1]["rerank_score"]

    def test_adds_rerank_score_key(self):
        client = make_mock_client("7")
        results = rerank(client, "query", PASSAGES, top_k=4)
        for r in results:
            assert "rerank_score" in r
            assert isinstance(r["rerank_score"], float)

    def test_preserves_original_keys(self):
        client = make_mock_client("5")
        results = rerank(client, "query", PASSAGES[:1], top_k=1)
        assert results[0]["id"] == "p1"
        assert "text" in results[0]


class TestTwoStageRetrieve:
    def test_full_pipeline(self):
        client = make_mock_client("7")

        def mock_retrieve(query, top_k):
            return PASSAGES[:top_k]

        results = two_stage_retrieve(
            client, "reactor", mock_retrieve, retrieve_k=4, final_k=2,
        )
        assert len(results) == 2

    def test_calls_retrieve_fn(self):
        client = make_mock_client("5")
        retrieve_fn = MagicMock(return_value=PASSAGES[:2])
        two_stage_retrieve(client, "test", retrieve_fn, retrieve_k=2, final_k=1)
        retrieve_fn.assert_called_once_with("test", 2)
