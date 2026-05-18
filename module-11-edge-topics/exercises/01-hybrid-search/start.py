"""
Exercise 01 — Hybrid Search

Combine BM25 keyword search with vector search using
Reciprocal Rank Fusion (RRF) to merge ranked result lists.

TODO: Implement each function below.
"""

import math


def tokenize(text: str) -> list[str]:
    """Lowercase and split text into tokens."""
    raise NotImplementedError


def bm25_search(
    query: str,
    documents: list[dict],
    top_k: int = 10,
) -> list[str]:
    """
    Simple BM25-style keyword search.

    Each document is a dict with "id" and "text" keys.
    Returns a ranked list of document IDs (most relevant first).

    Steps:
      1. Tokenize the query.
      2. Compute document frequency (df) for each token.
      3. Score each document using TF * IDF.
      4. Return the top_k document IDs sorted by score.
    """
    raise NotImplementedError


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    For each document, the RRF score is the sum of 1/(k + rank)
    across all lists where it appears (rank is 1-based).

    Returns a list of (doc_id, score) tuples sorted by score descending.
    """
    raise NotImplementedError


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    raise NotImplementedError


def vector_search(
    query_embedding: list[float],
    document_embeddings: dict[str, list[float]],
    top_k: int = 10,
) -> list[str]:
    """
    Simple cosine similarity vector search.
    Returns ranked list of document IDs.
    """
    raise NotImplementedError


def hybrid_search(
    query: str,
    documents: list[dict],
    query_embedding: list[float],
    document_embeddings: dict[str, list[float]],
    top_k: int = 5,
    rrf_k: int = 60,
) -> list[tuple[str, float]]:
    """
    Run BM25 and vector search, then fuse results with RRF.
    """
    raise NotImplementedError
