"""Part 5: A paraphrase of a cached question should hit, not call the model again."""

import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def demo_semantic_caching():
    print("=" * 60)
    print("PART 5: SEMANTIC CACHE")
    print("=" * 60)
    print()

    client = OpenAI()
    cache: list[dict] = []

    def embed(text):
        return client.embeddings.create(
            model="text-embedding-3-small", input=text
        ).data[0].embedding

    def cache_get(query):
        query_emb = embed(query)
        best_sim = -1.0
        best_resp = None
        for entry in cache:
            sim = cosine_similarity(query_emb, entry["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_resp = entry["response"]
        if best_sim >= 0.92:
            return best_resp, best_sim
        return None, best_sim

    def cache_set(query, response):
        cache.append({"query": query, "embedding": embed(query), "response": response})

    queries = [
        "What is the reactor temperature?",
        "How hot is the reactor?",
        "Tell me about reactor thermal readings",
        "What is the crew size?",
    ]
    cache_set(queries[0], "The reactor operates at 5000K.")
    cache_set("How many crew members are there?", "42 personnel aboard.")
    print(f"Cache seeded with {len(cache)} entries.\n")

    for query in queries:
        start = time.time()
        hit, sim = cache_get(query)
        elapsed = (time.time() - start) * 1000
        if hit:
            print(f"  CACHE HIT  (sim={sim:.3f}, {elapsed:.0f}ms)")
            print(f"  Q: '{query}'")
            print(f"  A: '{hit}'\n")
        else:
            print(f"  CACHE MISS (sim={sim:.3f}, {elapsed:.0f}ms)")
            print(f"  Q: '{query}'")
            print("  → Would call LLM here.\n")


if __name__ == "__main__":
    demo_semantic_caching()
