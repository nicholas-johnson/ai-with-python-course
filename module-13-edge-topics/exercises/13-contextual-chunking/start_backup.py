"""
Exercise 13 — Contextual Chunking

Implement multiple chunking strategies: fixed, overlapping,
and parent-child, then retrieve with parent context.
"""

import math


def fixed_chunk(text: str, chunk_size: int = 100) -> list[str]:
    """
    Split text into fixed-size word chunks.

    Args:
        text: The input text.
        chunk_size: Number of words per chunk.

    Returns:
        List of chunk strings.

    TODO:
    - Split text into words
    - Group words into chunks of chunk_size
    - Join each group back into a string
    - Return the list of chunk strings
    """
    # TODO: implement fixed chunking
    pass


def overlap_chunk(
    text: str,
    chunk_size: int = 100,
    overlap: int = 20,
) -> list[str]:
    """
    Split text into chunks with overlapping windows.

    Args:
        text: The input text.
        chunk_size: Number of words per chunk.
        overlap: Number of words to overlap between consecutive chunks.

    Returns:
        List of chunk strings.

    TODO:
    - Split text into words
    - Step through with stride = chunk_size - overlap
    - Each chunk takes chunk_size words from the current position
    - Return non-empty chunks
    """
    # TODO: implement overlapping chunking
    pass


def parent_child_chunk(
    text: str,
    parent_size: int = 200,
    child_size: int = 50,
) -> list[dict]:
    """
    Two-level parent-child chunking.

    First split into parent chunks, then split each parent into children.
    Each child knows its parent ID so you can retrieve the full parent context.

    Returns a list of dicts:
    {
        "child_text": str,
        "parent_id": int,
        "parent_text": str,
    }

    TODO:
    - Split text into words
    - Create parent chunks of parent_size words
    - For each parent, create child chunks of child_size words
    - Each child stores a reference to its parent_id and parent_text
    - Return the list of child dicts
    """
    # TODO: implement parent-child chunking
    pass


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve_with_context(
    query_embedding: list[float],
    child_chunks: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Search child chunks and return unique parent chunks for context.

    Each child_chunk dict has: "child_text", "parent_id", "parent_text", "embedding".

    Args:
        query_embedding: The query vector.
        child_chunks: List of child chunk dicts with embeddings.
        top_k: Number of parent contexts to return.

    Returns:
        List of unique parent chunk dicts:
        {"parent_id": int, "parent_text": str, "best_child_score": float}
        sorted by best_child_score descending.

    TODO:
    - Compute similarity between query and each child chunk's embedding
    - Group by parent_id, keeping the highest child score per parent
    - Sort by best_child_score descending
    - Return top_k unique parent contexts
    """
    # TODO: implement contextual retrieval
    pass
