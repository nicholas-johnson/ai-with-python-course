"""
Module 11 — Edge Topics: Interactive Demo

Demonstrates four high-impact patterns:
1. Hybrid search with Reciprocal Rank Fusion
2. Agentic RAG with tool-use
3. Citation verification
4. Semantic caching

Run: python module-11-edge-topics/demo/demo.py
Requires: OPENAI_API_KEY environment variable
"""

import json
import math
import time
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def separator(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


DOCUMENTS = [
    {"id": "doc1", "text": "The reactor core operates at 5000 degrees Kelvin under normal conditions. Cooling system uses liquid helium."},
    {"id": "doc2", "text": "Hull integrity on deck 5 is at 94% following the micrometeorite impact on stardate 4523.7."},
    {"id": "doc3", "text": "Navigation systems underwent maintenance on stardate 4520. All star charts updated to current sector."},
    {"id": "doc4", "text": "The crew complement is 42 personnel: 12 officers, 20 enlisted, 10 civilian scientists."},
    {"id": "doc5", "text": "Emergency protocol FTL-4092 requires immediate reactor shutdown if core temperature exceeds 6000K."},
    {"id": "doc6", "text": "Fuel reserves are at 73%. Next resupply scheduled at Station Omega in 14 days."},
    {"id": "doc7", "text": "The ship's AI system uses a retrieval-augmented generation pipeline for crew queries."},
    {"id": "doc8", "text": "Deck 7 was sealed after a coolant leak. Repair crew dispatched, ETA 6 hours."},
]


# ---------------------------------------------------------------------------
# Demo 1: Hybrid Search with RRF
# ---------------------------------------------------------------------------

def demo_hybrid_search() -> None:
    separator("Demo 1: Hybrid Search with Reciprocal Rank Fusion")

    print("We have 8 ship documents. Let's search with both keyword and")
    print("vector approaches, then fuse the results.\n")

    query = "reactor temperature emergency protocol"
    print(f"Query: '{query}'\n")

    def bm25_search(query: str) -> list[str]:
        query_tokens = set(query.lower().split())
        scores = {}
        for doc in DOCUMENTS:
            doc_tokens = set(doc["text"].lower().split())
            scores[doc["id"]] = len(query_tokens & doc_tokens)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _ in ranked]

    keyword_results = bm25_search(query)
    print("Keyword (BM25) ranking:")
    for i, doc_id in enumerate(keyword_results[:5], 1):
        doc = next(d for d in DOCUMENTS if d["id"] == doc_id)
        print(f"  {i}. [{doc_id}] {doc['text'][:60]}...")

    print()

    client = OpenAI()
    query_emb = client.embeddings.create(
        model="text-embedding-3-small", input=query,
    ).data[0].embedding

    doc_embs = {}
    for doc in DOCUMENTS:
        emb = client.embeddings.create(
            model="text-embedding-3-small", input=doc["text"],
        ).data[0].embedding
        doc_embs[doc["id"]] = emb

    vector_ranked = sorted(
        doc_embs.items(),
        key=lambda x: cosine_similarity(query_emb, x[1]),
        reverse=True,
    )
    vector_results = [doc_id for doc_id, _ in vector_ranked]

    print("Vector (semantic) ranking:")
    for i, doc_id in enumerate(vector_results[:5], 1):
        doc = next(d for d in DOCUMENTS if d["id"] == doc_id)
        sim = cosine_similarity(query_emb, doc_embs[doc_id])
        print(f"  {i}. [{doc_id}] (sim={sim:.3f}) {doc['text'][:50]}...")

    print()

    scores: dict[str, float] = {}
    k = 60
    for ranked_list in [keyword_results, vector_results]:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print("Hybrid (RRF) ranking:")
    for i, (doc_id, score) in enumerate(fused[:5], 1):
        doc = next(d for d in DOCUMENTS if d["id"] == doc_id)
        print(f"  {i}. [{doc_id}] (rrf={score:.5f}) {doc['text'][:50]}...")

    print("\n✓ RRF merges both rankings without needing to normalise scores.\n")
    input("Press Enter to continue...")


# ---------------------------------------------------------------------------
# Demo 2: Agentic RAG
# ---------------------------------------------------------------------------

def demo_agentic_rag() -> None:
    separator("Demo 2: Agentic RAG — The Agent Decides When to Search")

    client = OpenAI()

    def search_fn(query: str) -> list[dict]:
        query_emb = client.embeddings.create(
            model="text-embedding-3-small", input=query,
        ).data[0].embedding
        scored = []
        for doc in DOCUMENTS:
            emb = client.embeddings.create(
                model="text-embedding-3-small", input=doc["text"],
            ).data[0].embedding
            sim = cosine_similarity(query_emb, emb)
            scored.append({"id": doc["id"], "text": doc["text"], "score": round(sim, 3)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:3]

    tools = [{
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search ship documents for relevant information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                },
                "required": ["query"],
            },
        },
    }]

    question = "What is the reactor temperature and is there an emergency protocol if it gets too hot?"
    print(f"Question: '{question}'\n")
    print("The agent will decide what to search for...\n")

    messages = [
        {"role": "system", "content": "Answer questions about the ship using the search tool when needed."},
        {"role": "user", "content": question},
    ]

    for turn in range(3):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                print(f"  🔍 Agent searches: '{args['query']}'")
                results = search_fn(args["query"])
                for r in results[:2]:
                    print(f"     → [{r['id']}] (score={r['score']}) {r['text'][:50]}...")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(results),
                })
            print()
        else:
            print(f"Agent's answer:\n  {msg.content}\n")
            break

    print("✓ The agent decided what to search for and when it had enough info.\n")
    input("Press Enter to continue...")


# ---------------------------------------------------------------------------
# Demo 3: Citation Verification
# ---------------------------------------------------------------------------

def demo_citation_verification() -> None:
    separator("Demo 3: Citation Verification")

    client = OpenAI()

    passages = [
        "The reactor core operates at 5000 degrees Kelvin under normal conditions.",
        "The crew complement is 42 personnel.",
        "Hull integrity on deck 5 is at 94%.",
    ]

    answer = (
        "The reactor operates at 5000K. The ship has a crew of 42 people. "
        "The shields are at maximum power. Hull integrity on deck 5 is 94%."
    )

    print("Generated answer:")
    print(f"  '{answer}'\n")
    print("Source passages:")
    for i, p in enumerate(passages, 1):
        print(f"  [{i}] {p}")
    print()

    print("Extracting claims...")
    extract_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Extract each factual claim as a separate line:\n\n{answer}",
        }],
        temperature=0,
    )
    claims = [c.strip() for c in extract_resp.choices[0].message.content.split("\n") if c.strip()]
    print(f"  Found {len(claims)} claims:\n")

    for claim in claims:
        supported = False
        source = None
        for passage in passages:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Does this passage support this claim? "
                        f"Answer 'supported' or 'unsupported'.\n\n"
                        f"Claim: {claim}\nPassage: {passage}"
                    ),
                }],
                temperature=0,
            )
            verdict = resp.choices[0].message.content.strip().lower()
            if "supported" in verdict and "unsupported" not in verdict:
                supported = True
                source = passage[:40]
                break

        icon = "✅" if supported else "❌"
        src = f" ← '{source}...'" if source else ""
        print(f"  {icon} {claim}{src}")

    print("\n✓ Unsupported claims flagged — the shields claim has no source.\n")
    input("Press Enter to continue...")


# ---------------------------------------------------------------------------
# Demo 4: Semantic Caching
# ---------------------------------------------------------------------------

def demo_semantic_caching() -> None:
    separator("Demo 4: Semantic Caching")

    client = OpenAI()

    cache: list[dict] = []

    def embed(text):
        return client.embeddings.create(
            model="text-embedding-3-small", input=text,
        ).data[0].embedding

    def cache_get(query):
        q_emb = embed(query)
        best_sim = -1
        best_resp = None
        for entry in cache:
            sim = cosine_similarity(q_emb, entry["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_resp = entry["response"]
        if best_sim >= 0.92:
            return best_resp, best_sim
        return None, best_sim

    def cache_set(query, response):
        cache.append({
            "query": query,
            "embedding": embed(query),
            "response": response,
        })

    queries = [
        "What is the reactor temperature?",
        "How hot is the reactor?",
        "Tell me about reactor thermal readings",
        "What is the crew size?",
    ]

    cache_set(queries[0], "The reactor operates at 5000K.")
    cache_set("How many crew members are there?", "42 personnel aboard.")
    print(f"Cache seeded with {len(cache)} entries.\n")

    for q in queries:
        start = time.time()
        hit, sim = cache_get(q)
        elapsed = (time.time() - start) * 1000

        if hit:
            print(f"  CACHE HIT  (sim={sim:.3f}, {elapsed:.0f}ms)")
            print(f"  Q: '{q}'")
            print(f"  A: '{hit}'\n")
        else:
            print(f"  CACHE MISS (sim={sim:.3f}, {elapsed:.0f}ms)")
            print(f"  Q: '{q}'")
            print(f"  → Would call LLM here.\n")

    print("✓ Paraphrased queries hit the cache, saving LLM calls.\n")
    input("Press Enter to finish.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: Set OPENAI_API_KEY environment variable.")
        return

    print("\n" + "="*60)
    print("  Module 11 — Edge Topics: Interactive Demo")
    print("="*60)
    print("\nThis demo walks through four high-impact patterns:")
    print("  1. Hybrid search with Reciprocal Rank Fusion")
    print("  2. Agentic RAG with tool-use")
    print("  3. Citation verification")
    print("  4. Semantic caching")
    print()
    input("Press Enter to start...\n")

    demo_hybrid_search()
    demo_agentic_rag()
    demo_citation_verification()
    demo_semantic_caching()

    separator("Demo Complete")
    print("Key takeaways:")
    print("  • Hybrid search combines keyword + vector for robust retrieval")
    print("  • Agentic RAG lets the LLM decide when and what to retrieve")
    print("  • Citation verification catches unsupported claims")
    print("  • Semantic caching saves cost on paraphrased queries")
    print()


if __name__ == "__main__":
    main()
