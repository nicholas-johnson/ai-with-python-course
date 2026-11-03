"""Part 3: Deciding what to write, and superseding what a new fact replaces.
Needs OPENAI_API_KEY and the rag extra for ChromaDB.
Run alone:  python module-07-agent-memory/demo/03_memory_writer.py
"""

import time

from dotenv import load_dotenv
from openai import OpenAI

from memory_store import MemoryStore
from memory_writer import propose_memories, write_candidates

load_dotenv()

DAY = 86_400

# What the store already holds when the evening starts.
EXISTING = [
    ("Zara takes the Comet Tail with extra fizz.", "preference", 0.9, 40),
    ("Zara prefers her briefings short.", "preference", 0.8, 60),
]

# Three turns the writer should ignore, two it should keep, one that
# contradicts something already stored.
TURNS = [
    "What have you got on tap tonight?",
    "I am waiting on my crewmate, so just water for now.",
    "Actually, from now on give me the full detail on everything — I would rather have too much than miss something.",
    "Cheers. Busy station tonight.",
    "Worth knowing: I am the quartermaster on the Pathfinder, so tabs can go to the ship.",
]


def demo_memory_writer(client: OpenAI | None = None):
    client = client or OpenAI()

    print("=" * 60)
    print("PART 3: THE MEMORY WRITER")
    print("=" * 60)
    print()

    store = MemoryStore(client)
    now = time.time()
    for text, kind, importance, age_days in EXISTING:
        store.remember(
            text, patron="zara", kind=kind, importance=importance, written_at=now - age_days * DAY
        )

    print("  Already stored:")
    for row in store.all_active(patron="zara"):
        print(f"    - {row['text']}")
    print()

    print("-" * 60)
    print("  Each turn goes to the writer. Most turns should produce nothing.")
    print("-" * 60)
    print()

    for turn in TURNS:
        print(f'  Turn: "{turn}"')
        candidates = propose_memories(turn, client, patron="Zara")
        if not candidates:
            print("    -> nothing durable here\n")
            continue
        for candidate in candidates:
            print(
                f"    -> [{candidate.kind}] importance {candidate.importance:.2f}: "
                f"{candidate.text}"
            )
        # Writing is a second step: recall the neighbours, store, then settle
        # any conflict the new fact creates.
        write_candidates(candidates, store, patron="zara", client=client, verbose=True)
        print()

    print("-" * 60)
    print("  Live memories now:")
    print("-" * 60)
    for row in store.all_active(patron="zara"):
        print(f"    - {row['text']}")

    print()
    print('  "Prefers her briefings short" is gone — not deleted, superseded.')
    print("  The row survives with active=False and the id of what replaced it,")
    print("  so you can still answer what the agent believed and when.")
    print()
    print("  Append instead of supersede and the prompt would now carry both")
    print("  instructions at once. The model picks one at random each turn and")
    print("  the agent looks broken.")
    print()


if __name__ == "__main__":
    demo_memory_writer()
