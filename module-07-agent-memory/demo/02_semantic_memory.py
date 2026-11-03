"""Part 2: Semantic recall, scored — and keyed lookup failing on the same data.
Needs OPENAI_API_KEY (embeddings) and the rag extra for ChromaDB.
Run alone:  python module-07-agent-memory/demo/02_semantic_memory.py
"""

import time

from dotenv import load_dotenv
from openai import OpenAI

from memory_store import MemoryStore

load_dotenv()

DAY = 86_400

# text, key, kind, importance, age in days. The keys are the old-fashioned
# topic labels; nothing in recall uses them.
SEED = [
    ("Zara takes the Comet Tail with extra fizz.", "favourite_beverage", "preference", 0.9, 40),
    ("Zara is the quartermaster on the Pathfinder.", "role_assignment", "identity", 0.8, 120),
    ("Zara reacts badly to synthcitrus in any form.", "medical_note", "constraint", 1.0, 210),
    ("Zara prefers her briefings short.", "comms_style", "preference", 0.6, 11),
    ("Zara asked to be told when the Pathfinder Sour is back in stock.", "open_request", "commitment", 0.5, 2),
    ("Zara's shore leave ends on stardate 2288.4.", "schedule_note", "commitment", 0.4, 6),
]

QUERIES = [
    "What do I usually drink?",
    "Make me something citrus-forward, would you?",
    "Did I ask you to flag anything for me?",
]


def seed_store(client: OpenAI) -> MemoryStore:
    store = MemoryStore(client)
    now = time.time()
    for text, key, kind, importance, age_days in SEED:
        store.remember(
            text,
            patron="zara",
            kind=kind,
            importance=importance,
            written_at=now - age_days * DAY,
            key=key,
        )
    return store


def demo_semantic_memory(client: OpenAI | None = None):
    client = client or OpenAI()

    print("=" * 60)
    print("PART 2: SEMANTIC MEMORY")
    print("=" * 60)
    print()
    print(f"  Seeding {len(SEED)} memories for patron 'zara', ages 2 to 210 days...")
    store = seed_store(client)
    print("  Done. Each turn below is used as the retrieval query.\n")

    for query in QUERIES:
        print("-" * 60)
        print(f'  Turn: "{query}"')
        print("-" * 60)
        results = store.recall(query, patron="zara", k=3)
        print(f"    {'score':>6} {'relev':>6} {'recen':>6} {'import':>6}  memory")
        for memory in results:
            print(
                f"    {memory.score:>6.3f} {memory.relevance:>6.3f} "
                f"{memory.recency:>6.3f} {memory.importance:>6.2f}  {memory.text}"
            )
        print()

    print("=" * 60)
    print("  The same store, looked up by key")
    print("=" * 60)
    print()
    print('  A patron asks "what do I usually drink?". The keyed system goes')
    print('  looking for memories filed under "drink_":\n')

    keyed = store.prefix_recall("drink_", patron="zara")
    print(f"    prefix_recall('drink_') -> {len(keyed)} results")
    print("\n  Nothing. The memory exists, filed under 'favourite_beverage'.")
    print("  Semantic recall found it on the first query above, because it")
    print("  matches on meaning rather than on whatever label you chose")
    print("  six months ago.\n")

    print("  Three things worth noticing in the scores:")
    print("    - The synthcitrus constraint is 210 days old, so its recency is")
    print("      0.008 — and it still comes first on the citrus query. Relevance")
    print("      and importance carry it. Decay as a delete would have binned it.")
    print("    - The open request is 2 days old, so recency pushes it up whenever")
    print("      the query is vague.")
    print("    - Relevance is normalised across the candidates, not used raw.")
    print("      Raw cosine similarity here spans 0.03 to 0.38; blended against")
    print("      a recency term that spans 0 to 1, recency would win every time.")
    print()


if __name__ == "__main__":
    demo_semantic_memory()
