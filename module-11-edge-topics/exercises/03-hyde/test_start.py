"""Tests for Exercise 03 — HyDE."""

from unittest.mock import MagicMock
from start import generate_hypothetical_document, embed_text, hyde_search


def make_mock_client(chat_text="A hypothetical answer about the topic.", embedding=None):
    if embedding is None:
        embedding = [0.1] * 10
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


def make_mock_collection(results=None):
    if results is None:
        results = {
            "ids": [["doc1", "doc2"]],
            "documents": [["First document", "Second document"]],
            "distances": [[0.1, 0.3]],
        }
    collection = MagicMock()
    collection.query.return_value = results
    return collection


class TestGenerateHypotheticalDocument:
    def test_returns_string(self):
        client = make_mock_client("The reactor operates at high temperatures.")
        result = generate_hypothetical_document(client, "How hot is the reactor?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calls_chat_api(self):
        client = make_mock_client()
        generate_hypothetical_document(client, "test query")
        client.chat.completions.create.assert_called_once()

    def test_passes_query_in_prompt(self):
        client = make_mock_client()
        generate_hypothetical_document(client, "reactor temperature")
        call_args = client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
        content = messages[0]["content"] if messages else ""
        assert "reactor temperature" in content


class TestEmbedText:
    def test_returns_list_of_floats(self):
        client = make_mock_client(embedding=[0.1, 0.2, 0.3])
        result = embed_text(client, "test text")
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_calls_embedding_api(self):
        client = make_mock_client()
        embed_text(client, "test text")
        client.embeddings.create.assert_called_once()


class TestHydeSearch:
    def test_returns_dict_with_expected_keys(self):
        client = make_mock_client()
        collection = make_mock_collection()
        result = hyde_search(client, "test query", collection)
        assert isinstance(result, dict)
        assert "hypothetical_document" in result
        assert "results" in result

    def test_hypothetical_document_is_string(self):
        client = make_mock_client("Generated answer text")
        collection = make_mock_collection()
        result = hyde_search(client, "test", collection)
        assert result["hypothetical_document"] == "Generated answer text"

    def test_queries_collection_with_embedding(self):
        embedding = [0.5, 0.5, 0.5]
        client = make_mock_client(embedding=embedding)
        collection = make_mock_collection()
        hyde_search(client, "query", collection, n_results=3)
        collection.query.assert_called_once()
        call_kwargs = collection.query.call_args.kwargs
        assert call_kwargs["query_embeddings"] == [embedding]
        assert call_kwargs["n_results"] == 3

    def test_full_pipeline_integrates(self):
        client = make_mock_client(
            chat_text="A detailed answer",
            embedding=[0.1, 0.2],
        )
        collection = make_mock_collection()
        result = hyde_search(client, "question", collection)
        assert result["hypothetical_document"] == "A detailed answer"
        assert result["results"] is not None
