"""Tests for Exercise 12 — Multimodal RAG."""

from unittest.mock import MagicMock, mock_open, patch
from start import embed_text, index_item, build_multimodal_index, search_index, cosine_similarity


def make_mock_client(chat_text="A detailed image description.", embedding=None):
    if embedding is None:
        embedding = [0.1, 0.2, 0.3]
    client = MagicMock()

    chat_response = MagicMock()
    chat_response.choices = [MagicMock()]
    chat_response.choices[0].message.content = chat_text

    emb_response = MagicMock()
    emb_data = MagicMock()
    emb_data.embedding = embedding
    emb_response.data = [emb_data]

    client.chat.completions.create.return_value = chat_response
    client.embeddings.create.return_value = emb_response
    return client


class TestCoseSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-9

    def test_orthogonal_vectors(self):
        assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9


class TestEmbedText:
    def test_returns_list(self):
        client = make_mock_client(embedding=[0.1, 0.2])
        result = embed_text(client, "test")
        assert isinstance(result, list)

    def test_calls_api(self):
        client = make_mock_client()
        embed_text(client, "text")
        client.embeddings.create.assert_called_once()


class TestIndexItem:
    def test_text_item(self):
        client = make_mock_client(embedding=[0.1, 0.2, 0.3])
        item = {"id": "t1", "type": "text", "content": "Reactor report"}
        result = index_item(client, item)
        assert result["id"] == "t1"
        assert result["type"] == "text"
        assert result["text"] == "Reactor report"
        assert "embedding" in result
        assert isinstance(result["embedding"], list)

    def test_image_item(self):
        client = make_mock_client(
            chat_text="A diagram of the reactor",
            embedding=[0.4, 0.5, 0.6],
        )
        item = {"id": "i1", "type": "image", "path": "/fake/image.png"}

        with patch("builtins.open", mock_open(read_data=b"fake image data")):
            result = index_item(client, item)

        assert result["id"] == "i1"
        assert result["type"] == "image"
        assert result["text"] == "A diagram of the reactor"
        assert result["source"] == "/fake/image.png"

    def test_returns_embedding(self):
        emb = [0.7, 0.8, 0.9]
        client = make_mock_client(embedding=emb)
        item = {"id": "t2", "type": "text", "content": "Test"}
        result = index_item(client, item)
        assert result["embedding"] == emb


class TestBuildMultimodalIndex:
    def test_indexes_all_items(self):
        client = make_mock_client(embedding=[0.1, 0.2])
        items = [
            {"id": "t1", "type": "text", "content": "Text content"},
            {"id": "t2", "type": "text", "content": "More text"},
        ]
        index = build_multimodal_index(client, items)
        assert len(index) == 2
        assert index[0]["id"] == "t1"
        assert index[1]["id"] == "t2"

    def test_empty_items(self):
        client = make_mock_client()
        index = build_multimodal_index(client, [])
        assert index == []


class TestSearchIndex:
    def test_returns_ranked_results(self):
        client = make_mock_client(embedding=[0.9, 0.1, 0.0])
        index = [
            {"id": "d1", "text": "Reactor", "embedding": [0.9, 0.1, 0.0], "type": "text", "source": ""},
            {"id": "d2", "text": "Hull", "embedding": [0.0, 0.9, 0.1], "type": "text", "source": ""},
            {"id": "d3", "text": "Engine", "embedding": [0.8, 0.2, 0.0], "type": "text", "source": ""},
        ]
        results = search_index(client, "reactor status", index, top_k=2)
        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]

    def test_results_have_score(self):
        client = make_mock_client(embedding=[0.5, 0.5, 0.0])
        index = [{"id": "d1", "text": "Test", "embedding": [0.5, 0.5, 0.0], "type": "text", "source": ""}]
        results = search_index(client, "query", index, top_k=1)
        assert "score" in results[0]
        assert isinstance(results[0]["score"], float)

    def test_respects_top_k(self):
        client = make_mock_client(embedding=[0.5, 0.5, 0.0])
        index = [
            {"id": f"d{i}", "text": "T", "embedding": [0.1 * i, 0.2, 0.3], "type": "text", "source": ""}
            for i in range(10)
        ]
        results = search_index(client, "query", index, top_k=3)
        assert len(results) == 3
