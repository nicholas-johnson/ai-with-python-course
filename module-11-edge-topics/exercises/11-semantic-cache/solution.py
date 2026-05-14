"""
Exercise 11 — Semantic Caching (Solution)

Cache LLM responses by embedding similarity so paraphrased
questions return cached answers without making new API calls.
"""

import time
import math
from openai import OpenAI


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    """
    A cache that matches queries by embedding similarity.
    """

    def __init__(self, client: OpenAI, threshold: float = 0.95):
        self.client = client
        self.threshold = threshold
        self.entries: list[dict] = []

    def _embed(self, text: str) -> list[float]:
        """
        Get an embedding for text using OpenAI's embedding API.
        """
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def get(self, query: str) -> str | None:
        """
        Look up a query in the cache.
        """
        if not self.entries:
            return None

        query_emb = self._embed(query)
        best_sim = -1.0
        best_response = None

        for entry in self.entries:
            sim = cosine_similarity(query_emb, entry["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_response = entry["response"]

        if best_sim >= self.threshold:
            return best_response
        return None

    def set(self, query: str, response: str) -> None:
        """
        Store a query-response pair in the cache.
        """
        embedding = self._embed(query)
        self.entries.append({
            "query": query,
            "embedding": embedding,
            "response": response,
            "timestamp": time.time(),
        })

    def size(self) -> int:
        """Return the number of entries in the cache."""
        return len(self.entries)
