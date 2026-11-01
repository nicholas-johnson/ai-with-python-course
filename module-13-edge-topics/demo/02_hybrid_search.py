"""Part 2: Keyword search plus vector search, fused with RRF."""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DOCUMENTS = [
    {"id": "doc1", "text": "The reactor core operates at 5000K. Cooling uses liquid helium."},
    {"id": "doc2", "text": "Hull integrity on deck 5 is 94% after a micrometeorite impact."},
    {"id": "doc3", "text": "Navigation was serviced on stardate 4520. Star charts are current."},
    {"id": "doc4", "text": "The crew is 42: 12 officers, 20 enlisted, 10 civilian scientists."},
    {"id": "doc5", "text": "Protocol FTL-4092: shut down the reactor if the core exceeds 6000K."},
    {"id": "doc6", "text": "Fuel reserves are at 73%. Resupply at Station Omega in 14 days."},
    {"id": "doc7", "text": "The ship's AI answers crew queries with retrieval."},
    {"id": "doc8", "text": "Deck 7 is sealed after a coolant leak. Repair ETA is 6 hours."},
]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def demo_hybrid_search():
    print("=" * 60)
    print("PART 2: HYBRID SEARCH")
    print("=" * 60)
    print()

    query = "reactor temperature emergency protocol"
    print(f"Query: '{query}'\n")

    def bm25_search(text: str) -> list[str]:
        query_tokens = set(text.lower().split())
        scores = {}
        for doc in DOCUMENTS:
            doc_tokens = set(doc["text"].lower().split())
            scores[doc["id"]] = len(query_tokens & doc_tokens)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [doc_id for doc_id, _ in ranked]

    keyword_results = bm25_search(query)
    print("Keyword (BM25) ranking:")
    for i, doc_id in enumerate(keyword_results[:5], 1):
        doc = next(item for item in DOCUMENTS if item["id"] == doc_id)
        print(f"  {i}. [{doc_id}] {doc['text'][:60]}...")
    print()

    client = OpenAI()
    query_emb = client.embeddings.create(
        model="text-embedding-3-small", input=query
    ).data[0].embedding
    doc_embs = {}
    for doc in DOCUMENTS:
        emb = client.embeddings.create(
            model="text-embedding-3-small", input=doc["text"]
        ).data[0].embedding
        doc_embs[doc["id"]] = emb

    vector_results = [
        doc_id
        for doc_id, _ in sorted(
            doc_embs.items(),
            key=lambda item: cosine_similarity(query_emb, item[1]),
            reverse=True,
        )
    ]

    print("Vector (semantic) ranking:")
    for i, doc_id in enumerate(vector_results[:5], 1):
        doc = next(item for item in DOCUMENTS if item["id"] == doc_id)
        sim = cosine_similarity(query_emb, doc_embs[doc_id])
        print(f"  {i}. [{doc_id}] (sim={sim:.3f}) {doc['text'][:50]}...")
    print()

    scores: dict[str, float] = {}
    k = 60
    for ranked_list in [keyword_results, vector_results]:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    print("Hybrid (RRF) ranking:")
    for i, (doc_id, score) in enumerate(fused[:5], 1):
        doc = next(item for item in DOCUMENTS if item["id"] == doc_id)
        print(f"  {i}. [{doc_id}] (rrf={score:.5f}) {doc['text'][:50]}...")
    print()
