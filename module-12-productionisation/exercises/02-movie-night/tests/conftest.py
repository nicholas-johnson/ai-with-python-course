"""Shared fixtures for Movie Night tests."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


SAMPLE_MOVIES = [
    {
        "id": 1,
        "title": "The Shawshank Redemption",
        "year": 1994,
        "director": "Frank Darabont",
        "rating": 9.3,
        "runtime_minutes": 142,
        "plot": "A banker convicted of murder forms a friendship over years of imprisonment.",
        "genres": ["Drama"],
        "cast": ["Tim Robbins", "Morgan Freeman"],
    },
    {
        "id": 2,
        "title": "Inception",
        "year": 2010,
        "director": "Christopher Nolan",
        "rating": 8.8,
        "runtime_minutes": 148,
        "plot": "A thief who steals corporate secrets through dream-sharing technology.",
        "genres": ["Action", "Sci-Fi"],
        "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
    },
    {
        "id": 3,
        "title": "The Grand Budapest Hotel",
        "year": 2014,
        "director": "Wes Anderson",
        "rating": 8.1,
        "runtime_minutes": 99,
        "plot": "A concierge at a famous European hotel becomes entangled in theft and murder.",
        "genres": ["Comedy", "Drama"],
        "cast": ["Ralph Fiennes", "Tony Revolori"],
    },
]


@pytest.fixture(scope="session")
def data_dir(tmp_path_factory):
    """Create a temp data directory with sample movies.json and movies.db."""
    d = tmp_path_factory.mktemp("data")
    movies_path = d / "movies.json"
    movies_path.write_text(json.dumps(SAMPLE_MOVIES))
    return str(d)


@pytest.fixture(scope="session")
def app_client(data_dir):
    """Create a TestClient backed by the solution app with mocked AI calls."""
    db_path = os.path.join(data_dir, "movies.db")

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("solution.config.DATA_DIR", data_dir), \
             patch("solution.config.DB_PATH", db_path), \
             patch("solution.rag._get_embeddings") as mock_embed, \
             patch("solution.rag.client") as mock_rag_client, \
             patch("solution.sql.client") as mock_sql_client, \
             patch("solution.cache.client"):

            mock_embed.return_value = [[0.1] * 1536]

            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "ids": [["1", "2"]],
                "documents": [["Shawshank...", "Inception..."]],
                "metadatas": [[
                    {"title": "The Shawshank Redemption", "year": 1994,
                     "director": "Frank Darabont", "rating": 9.3, "genres": "Drama"},
                    {"title": "Inception", "year": 2010,
                     "director": "Christopher Nolan", "rating": 8.8, "genres": "Action, Sci-Fi"},
                ]],
                "distances": [[0.1, 0.2]],
            }

            rerank_response = MagicMock()
            rerank_response.choices = [MagicMock()]
            rerank_response.choices[0].message.content = "1,2"
            mock_rag_client.chat.completions.create.return_value = rerank_response

            sql_response = MagicMock()
            sql_response.choices = [MagicMock()]
            sql_response.choices[0].message.content = "SELECT title, year FROM movies"
            mock_sql_client.chat.completions.create.return_value = sql_response

            with patch("solution.rag.build_index", return_value=mock_collection):
                from solution.app import app
                client = TestClient(app)
                yield client
