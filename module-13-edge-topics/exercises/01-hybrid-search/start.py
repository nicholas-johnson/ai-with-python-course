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


def main() -> None:
    """Run hybrid search over a small sample corpus and print fused results."""
    documents = [
        {"id": "doc1", "text": "The reactor core temperature is rising rapidly"},
        {"id": "doc2", "text": "Hull integrity on deck 5 shows minor damage"},
        {"id": "doc3", "text": "Navigation systems are operating normally"},
        {"id": "doc4", "text": "The reactor cooling system needs maintenance"},
        {"id": "doc5", "text": "Emergency protocols for hull breach on deck 7"},
    ]
    document_embeddings = {
        "doc1": [0.9, 0.1, 0.0, 0.0],
        "doc2": [0.0, 0.8, 0.2, 0.0],
        "doc3": [0.0, 0.0, 0.9, 0.1],
        "doc4": [0.8, 0.2, 0.0, 0.0],
        "doc5": [0.1, 0.7, 0.1, 0.1],
    }
    query = "reactor temperature"
    query_embedding = [0.9, 0.1, 0.0, 0.0]

    results = hybrid_search(query, documents, query_embedding, document_embeddings)
    print(f"Query: {query!r}\n")
    for doc_id, score in results:
        text = next(d["text"] for d in documents if d["id"] == doc_id)
        print(f"{doc_id}  {score:.4f}  {text}")


if __name__ == "__main__":
    main()
