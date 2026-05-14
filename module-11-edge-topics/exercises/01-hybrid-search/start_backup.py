"""
Exercise 01 — Hybrid Search

Combine BM25 keyword search with vector search using
Reciprocal Rank Fusion (RRF) to merge ranked result lists.
"""

import math


def tokenize(text: str) -> list[str]:
    """Lowercase and split text into tokens."""
    return text.lower().split()


def bm25_search(
    query: str,
    documents: list[dict],
    top_k: int = 10,
) -> list[str]:
    """
    Simple BM25-style keyword search.

    Each document is a dict with "id" and "text" keys.
    Returns a ranked list of document IDs (most relevant first).

    TODO:
    - Tokenize the query
    - For each document, compute a relevance score based on
      how many query terms appear in the document (term frequency)
    - Weight by inverse document frequency: log(N / df) where df
      is the number of documents containing the term
    - Return the top_k document IDs sorted by score descending
    """
    # TODO: implement BM25 search
    pass


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    For each document, the RRF score is the sum of 1/(k + rank)
    across all lists where it appears (rank is 1-based).

    Args:
        ranked_lists: List of ranked document ID lists.
        k: RRF constant (default 60).

    Returns:
        List of (doc_id, score) tuples sorted by score descending.

    TODO:
    - Iterate over each ranked list
    - For each doc_id at position rank (1-based), add 1/(k+rank) to its score
    - Return all (doc_id, score) pairs sorted by score descending
    """
    # TODO: implement RRF
    pass


def vector_search(
    query_embedding: list[float],
    document_embeddings: dict[str, list[float]],
    top_k: int = 10,
) -> list[str]:
    """
    Simple cosine similarity vector search.

    Args:
        query_embedding: The query vector.
        document_embeddings: Dict mapping doc_id to embedding vector.
        top_k: Number of results to return.

    Returns:
        Ranked list of document IDs.

    TODO:
    - Compute cosine similarity between query and each document embedding
    - Return top_k doc IDs sorted by similarity descending
    """
    # TODO: implement vector search
    pass


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

    TODO:
    - Run bm25_search to get keyword-ranked results
    - Run vector_search to get semantic-ranked results
    - Fuse both lists with reciprocal_rank_fusion
    - Return top_k results
    """
    # TODO: implement hybrid search
    pass
