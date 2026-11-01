"""Test fixtures for the travel planner."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

# Point to solution for testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


SAMPLE_DESTINATIONS = [
    {
        "id": "tokyo",
        "name": "Tokyo",
        "country": "Japan",
        "description": "Vibrant metropolis blending ancient temples with cutting-edge technology",
        "tags": ["culture", "food", "technology", "shopping"],
        "safety_notes": "",
        "attractions": [
            {
                "name": "Senso-ji Temple",
                "description": "Ancient Buddhist temple in Asakusa, oldest in Tokyo",
                "category": "culture",
            },
            {
                "name": "Shibuya Crossing",
                "description": "World-famous pedestrian scramble crossing",
                "category": "landmark",
            },
        ],
    },
    {
        "id": "paris",
        "name": "Paris",
        "country": "France",
        "description": "City of lights, known for art, cuisine, and romantic architecture",
        "tags": ["art", "food", "romance", "history"],
        "safety_notes": "",
        "attractions": [
            {
                "name": "Eiffel Tower",
                "description": "Iconic iron lattice tower and symbol of France",
                "category": "landmark",
            },
            {
                "name": "Louvre Museum",
                "description": "World's largest art museum housing the Mona Lisa",
                "category": "art",
            },
        ],
    },
]


@pytest.fixture
def sample_destinations():
    return SAMPLE_DESTINATIONS


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for tests that don't need real API calls."""
    with patch("solution.rag.client") as mock_rag, \
         patch("solution.agent.client") as mock_agent:
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 1536
        mock_rag.embeddings.create.return_value = MagicMock(
            data=[mock_embedding] * 10
        )
        yield {"rag": mock_rag, "agent": mock_agent}
