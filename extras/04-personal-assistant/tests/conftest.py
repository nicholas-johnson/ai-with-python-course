"""Shared test fixtures for the personal assistant."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def data_dir():
    return os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture
def sample_notes(data_dir):
    with open(os.path.join(data_dir, "notes.json")) as f:
        return json.load(f)


@pytest.fixture
def sample_calendar(data_dir):
    with open(os.path.join(data_dir, "calendar.json")) as f:
        return json.load(f)


@pytest.fixture
def sample_reminders(data_dir):
    with open(os.path.join(data_dir, "reminders.json")) as f:
        return json.load(f)


@pytest.fixture
def mock_collection():
    """A mock ChromaDB collection for testing without real embeddings."""
    collection = MagicMock()
    collection.query.return_value = {
        "ids": [["note-001"]],
        "documents": [["Meeting notes: Q3 planning. Discussed roadmap priorities..."]],
        "metadatas": [[{"note_id": "note-001", "title": "Meeting notes: Q3 planning", "tags": "work, meetings"}]],
        "distances": [[0.25]],
    }
    return collection


@pytest.fixture
def test_client(mock_collection):
    """Create a FastAPI test client with mocked dependencies."""
    with patch("solution.rag.build_notes_index", return_value=mock_collection):
        from solution.app import app
        import solution.app as app_module

        app_module.notes_collection = mock_collection

        with TestClient(app) as client:
            yield client
