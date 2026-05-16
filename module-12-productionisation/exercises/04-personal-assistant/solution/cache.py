"""Semantic cache — avoids redundant API calls for similar queries."""

import time

import numpy as np
from openai import OpenAI

from .config import EMBEDDING_MODEL

client = OpenAI()


class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.92, ttl_seconds: int = 300):
        self.threshold = similarity_threshold
        self.ttl = ttl_seconds
        self.entries: list[dict] = []

    def _embed(self, text: str) -> list[float]:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
        return response.data[0].embedding

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a_arr, b_arr = np.array(a), np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def get(self, query: str) -> str | None:
        """Return cached result if a semantically similar query exists."""
        now = time.time()
        query_embedding = self._embed(query)

        best_match = None
        best_score = 0.0

        for entry in self.entries:
            if now - entry["timestamp"] > self.ttl:
                continue
            score = self._cosine_similarity(query_embedding, entry["embedding"])
            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score >= self.threshold:
            return best_match["result"]
        return None

    def set(self, query: str, result: str):
        """Store a query result in the cache."""
        embedding = self._embed(query)
        self.entries.append({
            "query": query,
            "embedding": embedding,
            "result": result,
            "timestamp": time.time(),
        })

        now = time.time()
        self.entries = [e for e in self.entries if now - e["timestamp"] <= self.ttl]
