"""Shared fixtures for Recipe Finder tests."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

SAMPLE_RECIPES = [
    {
        "id": "recipe-001",
        "title": "Classic Margherita Pizza",
        "description": "A simple Italian pizza with fresh tomatoes and mozzarella.",
        "cuisine": "Italian",
        "dietary": ["vegetarian"],
        "cook_time": "25 mins",
        "ingredients": ["pizza dough", "tomato sauce", "mozzarella", "fresh basil", "olive oil"],
        "instructions": ["Preheat oven to 450F.", "Spread sauce on dough.", "Add cheese and basil.", "Bake 12-15 mins."],
    },
    {
        "id": "recipe-002",
        "title": "Chicken Tikka Masala",
        "description": "Creamy spiced curry with tender chicken pieces.",
        "cuisine": "Indian",
        "dietary": ["gluten-free"],
        "cook_time": "40 mins",
        "ingredients": ["chicken breast", "yogurt", "tikka spice", "tomato puree", "cream", "rice"],
        "instructions": ["Marinate chicken.", "Grill until charred.", "Simmer in sauce.", "Serve with rice."],
    },
    {
        "id": "recipe-003",
        "title": "Vegan Buddha Bowl",
        "description": "A nourishing bowl with quinoa, roasted vegetables, and tahini dressing.",
        "cuisine": "International",
        "dietary": ["vegan", "gluten-free"],
        "cook_time": "30 mins",
        "ingredients": ["quinoa", "sweet potato", "chickpeas", "kale", "tahini", "lemon"],
        "instructions": ["Cook quinoa.", "Roast vegetables.", "Assemble bowl.", "Drizzle with tahini dressing."],
    },
]


@pytest.fixture
def sample_recipes():
    return SAMPLE_RECIPES


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for tests that don't need real API calls."""
    mock_embedding = [0.1] * 1536

    with patch("solution.rag.client") as mock_rag, \
         patch("solution.cache.client") as mock_cache:

        def fake_embeddings(*, input, **kwargs):
            # One vector per input text, like the real API.
            texts = [input] if isinstance(input, str) else input
            return MagicMock(data=[MagicMock(embedding=mock_embedding) for _ in texts])

        mock_rag.embeddings.create.side_effect = fake_embeddings
        mock_cache.embeddings.create.side_effect = fake_embeddings

        mock_rag.responses.parse.return_value = MagicMock(output_parsed=MagicMock(order=[1, 2, 3]))

        yield {"rag": mock_rag, "cache": mock_cache}
