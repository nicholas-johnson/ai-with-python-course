"""
Exercise 01 — Hybrid Search (Solution)

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
    """
    query_tokens = tokenize(query)
    n = len(documents)

    df: dict[str, int] = {}
    for doc in documents:
        doc_tokens = set(tokenize(doc["text"]))
        for token in doc_tokens:
            df[token] = df.get(token, 0) + 1

    scores: dict[str, float] = {}
    for doc in documents:
        doc_tokens = tokenize(doc["text"])
        token_counts: dict[str, int] = {}
        for t in doc_tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        score = 0.0
        for qt in query_tokens:
            if qt in token_counts:
                tf = token_counts[qt]
                idf = math.log((n + 1) / (df.get(qt, 0) + 1))
                score += tf * idf
        scores[doc["id"]] = score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in ranked[:top_k]]


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    For each document, the RRF score is the sum of 1/(k + rank)
    across all lists where it appears (rank is 1-based).
    """
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_search(
    query_embedding: list[float],
    document_embeddings: dict[str, list[float]],
    top_k: int = 10,
) -> list[str]:
    """
    Simple cosine similarity vector search.
    Returns ranked list of document IDs.
    """
    similarities = []
    for doc_id, emb in document_embeddings.items():
        sim = _cosine_similarity(query_embedding, emb)
        similarities.append((doc_id, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in similarities[:top_k]]


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
    keyword_results = bm25_search(query, documents)
    semantic_results = vector_search(query_embedding, document_embeddings)
    fused = reciprocal_rank_fusion([keyword_results, semantic_results], k=rrf_k)
    return fused[:top_k]


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
