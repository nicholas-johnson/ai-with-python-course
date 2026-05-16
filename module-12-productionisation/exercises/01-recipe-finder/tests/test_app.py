"""Tests for the Recipe Finder API."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from tests.conftest import SAMPLE_RECIPES


@pytest.fixture
def client(mock_openai, tmp_path):
    """Create a test client with mocked data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    recipes_file = data_dir / "recipes.json"
    recipes_file.write_text(json.dumps(SAMPLE_RECIPES))

    with patch("solution.config.DATA_DIR", str(data_dir)):
        with patch("solution.app.DATA_DIR", str(data_dir)):
            from solution.app import app
            test_client = TestClient(app)
            yield test_client


def test_health_endpoint(client):
    """GET /api/health should return 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "index_size" in data


def test_search_returns_results(client):
    """POST /api/search should return results list."""
    response = client.post("/api/search", json={"query": "pizza"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "cached" in data
    assert isinstance(data["results"], list)


def test_recipe_by_id(client):
    """GET /api/recipe/{id} should return the full recipe."""
    response = client.get("/api/recipe/recipe-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "recipe-001"
    assert data["title"] == "Classic Margherita Pizza"


def test_recipe_not_found(client):
    """GET /api/recipe/{id} should return 404 for unknown IDs."""
    response = client.get("/api/recipe/nonexistent")
    assert response.status_code == 404
