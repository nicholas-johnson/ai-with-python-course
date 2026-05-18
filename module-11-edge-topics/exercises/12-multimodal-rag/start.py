"""
Exercise 12 — Multimodal RAG

Index and search both text and images in a unified vector store
by describing images with a vision model before embedding.
"""

import math
from openai import OpenAI


def describe_image(client: OpenAI, image_path: str) -> str:
    """
    Use a vision model to generate a text description of an image.

    Args:
        client: OpenAI client.
        image_path: Path to the image file.

    Returns:
        A detailed text description of the image.

    TODO:
    - Read and base64-encode the image file
    - Send to gpt-4o-mini with a prompt asking for a detailed description
    - Use the image_url content type with the base64 data
    - Return the description text
    """
    # TODO: implement image description
    pass


def embed_text(client: OpenAI, text: str) -> list[float]:
    """
    Get an embedding vector for text.

    TODO:
    - Use text-embedding-3-small model
    - Return the embedding vector
    """
    # TODO: implement text embedding
    pass


def index_item(client: OpenAI, item: dict) -> dict:
    """
    Create an index entry for a text or image item.

    Items have:
    - "id": unique identifier
    - "type": "text" or "image"
    - "content": the text content (for text items)
    - "path": the file path (for image items)

    Returns an index entry with:
    - "id": the item id
    - "type": the item type
    - "text": the text (original for text, description for images)
    - "embedding": the embedding vector
    - "source": the original path (for images) or empty string

    TODO:
    - If type is "text", use the content directly
    - If type is "image", call describe_image to get text
    - Embed the text
    - Return the index entry dict
    """
    # TODO: implement item indexing
    pass


def build_multimodal_index(client: OpenAI, items: list[dict]) -> list[dict]:
    """
    Build a multimodal index from a list of text and image items.

    TODO:
    - Index each item using index_item
    - Return the list of index entries
    """
    # TODO: implement index building
    pass


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_index(
    client: OpenAI,
    query: str,
    index: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Search the multimodal index with a text query.

    Args:
        client: OpenAI client.
        query: Text query.
        index: List of index entries.
        top_k: Number of results to return.

    Returns:
        List of index entries sorted by relevance, with "score" added.

    TODO:
    - Embed the query
    - Compute similarity against each index entry
    - Sort by similarity descending
    - Return top_k results with "score" added to each
    """
    # TODO: implement index search
    pass
