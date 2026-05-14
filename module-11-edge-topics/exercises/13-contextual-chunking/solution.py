"""
Exercise 13 — Contextual Chunking (Solution)

Implement multiple chunking strategies: fixed, overlapping,
and parent-child, then retrieve with parent context.
"""

import math


def fixed_chunk(text: str, chunk_size: int = 100) -> list[str]:
    """
    Split text into fixed-size word chunks.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def overlap_chunk(
    text: str,
    chunk_size: int = 100,
    overlap: int = 20,
) -> list[str]:
    """
    Split text into chunks with overlapping windows.
    """
    words = text.split()
    chunks = []
    stride = chunk_size - overlap
    if stride <= 0:
        stride = 1
    for i in range(0, len(words), stride):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


def parent_child_chunk(
    text: str,
    parent_size: int = 200,
    child_size: int = 50,
) -> list[dict]:
    """
    Two-level parent-child chunking.
    """
    words = text.split()
    chunks = []
    parent_id = 0

    for parent_start in range(0, len(words), parent_size):
        parent_words = words[parent_start:parent_start + parent_size]
        parent_text = " ".join(parent_words)

        for child_start in range(0, len(parent_words), child_size):
            child_text = " ".join(parent_words[child_start:child_start + child_size])
            if child_text.strip():
                chunks.append({
                    "child_text": child_text,
                    "parent_id": parent_id,
                    "parent_text": parent_text,
                })
        parent_id += 1

    return chunks


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
    """
    parent_scores: dict[int, dict] = {}

    for child in child_chunks:
        sim = cosine_similarity(query_embedding, child["embedding"])
        pid = child["parent_id"]

        if pid not in parent_scores or sim > parent_scores[pid]["best_child_score"]:
            parent_scores[pid] = {
                "parent_id": pid,
                "parent_text": child["parent_text"],
                "best_child_score": sim,
            }

    ranked = sorted(parent_scores.values(), key=lambda x: x["best_child_score"], reverse=True)
    return ranked[:top_k]
