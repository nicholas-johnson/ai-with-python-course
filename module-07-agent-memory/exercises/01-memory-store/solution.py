"""
Exercise 01 — Memory Store (solution)
A semantic memory store for BARKEEP: scored recall, per-patron namespacing,
supersede on contradiction, soft-delete on request.

Run:  python solution.py
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
EMBED_MODEL = "text-embedding-3-small"

HALF_LIFE_DAYS = 30.0
RELEVANCE_WEIGHT = 0.6
RECENCY_WEIGHT = 0.25
IMPORTANCE_WEIGHT = 0.15
DAY_SECONDS = 86_400

CHROMA_PATH = str(Path(__file__).resolve().parent / "chroma_data")

MemoryKind = Literal["preference", "constraint", "identity", "commitment"]


@dataclass
class ScoredMemory:
    memory_id: str
    text: str
    kind: str
    importance: float
    written_at: float
    relevance: float
    recency: float
    score: float


def embed(text: str, client: OpenAI) -> list[float]:
    """Embed one string."""
    response = client.embeddings.create(model=EMBED_MODEL, input=[text])
    return response.data[0].embedding


def normalise(similarities: list[float]) -> list[float]:
    """Spread raw similarities across [0, 1] within the candidate set."""
    if not similarities:
        return []
    low, high = min(similarities), max(similarities)
    if high - low < 1e-9:
        return [1.0] * len(similarities)
    return [(s - low) / (high - low) for s in similarities]


def recency_weight(written_at: float, now: float | None = None) -> float:
    """Decay as a weight: half as much per half-life."""
    now = now if now is not None else time.time()
    age_days = max(0.0, (now - written_at) / DAY_SECONDS)
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def score_memory(
    relevance: float, written_at: float, importance: float, now: float | None = None
) -> tuple[float, float]:
    """Return (recency, combined score) for one candidate."""
    recency = recency_weight(written_at, now)
    combined = (
        RELEVANCE_WEIGHT * relevance
        + RECENCY_WEIGHT * recency
        + IMPORTANCE_WEIGHT * importance
    )
    return recency, combined


def build_collection(path: str = CHROMA_PATH):
    """A persistent Chroma collection using cosine distance."""
    return chromadb.PersistentClient(path=path).get_or_create_collection(
        "cantina_memories",
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )


class MemoryStore:
    """Semantic memory over a Chroma collection, namespaced per patron."""

    def __init__(self, client: OpenAI, collection):
        self.client = client
        self.collection = collection

    def remember(
        self,
        text: str,
        *,
        patron: str,
        kind: str = "preference",
        importance: float = 1.0,
        written_at: float | None = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        self.collection.add(
            ids=[memory_id],
            embeddings=[embed(text, self.client)],
            documents=[text],
            metadatas=[
                {
                    "patron": patron,
                    "kind": kind,
                    "importance": importance,
                    "written_at": written_at if written_at is not None else time.time(),
                    "active": True,
                    "superseded_by": "",
                }
            ],
        )
        return memory_id

    def recall(self, query: str, *, patron: str, k: int = 5) -> list[ScoredMemory]:
        results = self.collection.query(
            query_embeddings=[embed(query, self.client)],
            n_results=max(k * 4, k),
            where={"$and": [{"patron": {"$eq": patron}}, {"active": {"$eq": True}}]},
        )
        if not results["ids"] or not results["ids"][0]:
            return []

        similarities = [1.0 - distance for distance in results["distances"][0]]
        relevances = normalise(similarities)

        scored = []
        for memory_id, document, metadata, relevance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            relevances,
        ):
            recency, combined = score_memory(
                relevance, metadata["written_at"], metadata["importance"]
            )
            scored.append(
                ScoredMemory(
                    memory_id=memory_id,
                    text=document,
                    kind=metadata["kind"],
                    importance=metadata["importance"],
                    written_at=metadata["written_at"],
                    relevance=relevance,
                    recency=recency,
                    score=combined,
                )
            )

        scored.sort(key=lambda memory: memory.score, reverse=True)
        return scored[:k]

    def all_active(self, *, patron: str) -> list[dict]:
        results = self.collection.get(
            where={"$and": [{"patron": {"$eq": patron}}, {"active": {"$eq": True}}]}
        )
        rows = [
            {"memory_id": memory_id, "text": document, **metadata}
            for memory_id, document, metadata in zip(
                results["ids"], results["documents"], results["metadatas"]
            )
        ]
        rows.sort(key=lambda row: row["written_at"], reverse=True)
        return rows

    def _deactivate(self, memory_id: str, superseded_by: str = "") -> bool:
        existing = self.collection.get(ids=[memory_id])
        if not existing["ids"]:
            return False
        metadata = dict(existing["metadatas"][0])
        metadata["active"] = False
        metadata["superseded_by"] = superseded_by
        self.collection.update(ids=[memory_id], metadatas=[metadata])
        return True

    def supersede(self, memory_id: str, *, by: str) -> bool:
        """Retire a memory a newer one replaces, keeping the trail."""
        return self._deactivate(memory_id, superseded_by=by)

    def forget(self, memory_id: str) -> bool:
        """Soft-delete on request: stops reaching the model, stays auditable."""
        return self._deactivate(memory_id)


class MemoryCandidate(BaseModel):
    text: str = Field(description="The fact, as a standalone sentence naming the patron")
    kind: MemoryKind
    importance: float = Field(ge=0.0, le=1.0)


class WriteDecision(BaseModel):
    candidates: list[MemoryCandidate] = Field(
        description="Facts worth keeping. Empty when the turn holds nothing durable."
    )


class MergeDecision(BaseModel):
    action: Literal["store", "replace", "skip"]
    target: int = Field(default=-1, description="Index of the existing memory, or -1")
    reason: str


WRITE_PROMPT = """You decide what a bartender should remember about a patron.

Write a candidate only when the fact will still matter next week:
  preference  - a standing choice, e.g. a usual order
  constraint  - something that must always be respected, e.g. an allergy
  identity    - who the patron is, their role or ship
  commitment  - an open loop, e.g. an unpaid tab

Do not write one-off questions, transient state, or chitchat. Most turns
produce no candidates at all. Write each fact as a standalone sentence that
still makes sense months later, naming the patron."""

MERGE_PROMPT = """A new fact about a patron is about to be stored, alongside the
closest memories already held. Choose one action:

  replace - the new fact and an existing one cannot both be true. Give its index.
  skip    - an existing memory already says this, in equal or more detail.
  store   - genuinely new, or it adds detail the existing memories lack.

Prefer skip over store when the difference is only phrasing."""

PERSONA = (
    "You are BARKEEP, the AI bartender at The Nebula's Edge cantina on Relay "
    "Station Omicron. You are warm, slightly wry, and you take pride in never "
    "forgetting a regular. You never serve a patron something they have told you "
    "they cannot drink."
)


def resolve(text: str, neighbours: list[ScoredMemory], client: OpenAI) -> MergeDecision:
    """Decide whether a new fact is stored, replaces an existing one, or is a duplicate."""
    if not neighbours:
        return MergeDecision(action="store", reason="Nothing stored nearby.")

    listing = "\n".join(f"{i}: {memory.text}" for i, memory in enumerate(neighbours))
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=MergeDecision,
        input=[
            {"role": "system", "content": MERGE_PROMPT},
            {"role": "user", "content": f"New fact: {text}\n\nExisting memories:\n{listing}"},
        ],
    )
    decision = response.output_parsed
    if not decision:
        return MergeDecision(action="store", reason="No decision returned.")
    if decision.action in ("replace", "skip") and not 0 <= decision.target < len(neighbours):
        return MergeDecision(action="store", reason="Target out of range.")
    return decision


def propose_memories(user_input: str, patron: str, client: OpenAI) -> list[MemoryCandidate]:
    """Ask the model what, if anything, this turn is worth remembering."""
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=WriteDecision,
        input=[
            {"role": "system", "content": WRITE_PROMPT},
            {"role": "user", "content": f"Patron: {patron}\nThey said: {user_input}"},
        ],
    )
    decision = response.output_parsed
    return decision.candidates if decision else []


def write_memories(
    user_input: str, store: MemoryStore, patron: str, client: OpenAI
) -> list[str]:
    """Extract candidates, then store, replace, or skip each one."""
    written = []
    for candidate in propose_memories(user_input, patron, client):
        neighbours = store.recall(candidate.text, patron=patron, k=3)
        decision = resolve(candidate.text, neighbours, client)

        if decision.action == "skip":
            print(f'  [already known: "{candidate.text}"]')
            continue

        memory_id = store.remember(
            candidate.text,
            patron=patron,
            kind=candidate.kind,
            importance=candidate.importance,
        )
        written.append(memory_id)

        if decision.action == "replace":
            store.supersede(neighbours[decision.target].memory_id, by=memory_id)
            print(f'  [superseded: "{neighbours[decision.target].text}"]')
        print(f'  [remembered: "{candidate.text}"]')

    return written


def build_system_prompt(memories: list[ScoredMemory]) -> str:
    """The persona, plus whatever recall selected for this turn."""
    if not memories:
        return PERSONA + "\n\nYou have not met this patron before."
    block = "\n".join(f"- {memory.text}" for memory in memories)
    return PERSONA + f"\n\nWhat you remember about this patron:\n{block}"


def chat(
    user_input: str,
    thread: list[dict],
    store: MemoryStore,
    patron: str,
    client: OpenAI,
) -> str:
    """One turn: recall, answer, then write anything durable."""
    memories = store.recall(user_input, patron=patron, k=5)
    thread.append({"role": "user", "content": user_input})

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[{"role": "system", "content": build_system_prompt(memories)}, *thread],
    )
    reply = response.output_text
    thread.append({"role": "assistant", "content": reply})

    write_memories(user_input, store, patron, client)
    return reply


def main():
    client = OpenAI()
    store = MemoryStore(client, build_collection())
    patron = "zara"
    thread: list[dict] = []

    print("=== The Nebula's Edge — BARKEEP ===")
    print("Commands: /memories, /recall <query>, /forget <n>, /patron <name>, quit\n")
    print(f"Serving: {patron}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/memories":
            rows = store.all_active(patron=patron)
            if not rows:
                print(f"[No memories for {patron}]\n")
            else:
                for index, row in enumerate(rows):
                    age_days = (time.time() - row["written_at"]) / DAY_SECONDS
                    print(
                        f"  {index}. [{row['kind']}] {row['text']} "
                        f"(importance {row['importance']:.2f}, {age_days:.0f}d old)"
                    )
                print()
            continue

        if user_input.startswith("/recall "):
            query = user_input[len("/recall ") :].strip()
            results = store.recall(query, patron=patron, k=5)
            if not results:
                print("[Nothing recalled]\n")
            else:
                print(f"  {'score':>6} {'relev':>6} {'recen':>6} {'import':>6}  memory")
                for memory in results:
                    print(
                        f"  {memory.score:>6.3f} {memory.relevance:>6.3f} "
                        f"{memory.recency:>6.3f} {memory.importance:>6.2f}  {memory.text}"
                    )
                print()
            continue

        if user_input.startswith("/forget "):
            rows = store.all_active(patron=patron)
            try:
                row = rows[int(user_input.split()[1])]
            except (IndexError, ValueError):
                print("[No memory at that index — try /memories]\n")
                continue
            store.forget(row["memory_id"])
            print(f"[Forgot: {row['text']}]\n")
            continue

        if user_input.startswith("/patron "):
            patron = user_input.split()[1].strip().lower()
            thread = []
            print(f"[Now serving: {patron}. Fresh conversation, separate memories.]\n")
            continue

        print(f"Agent: {chat(user_input, thread, store, patron, client)}\n")


if __name__ == "__main__":
    main()
