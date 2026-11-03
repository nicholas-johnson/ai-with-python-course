"""
Exercise 01 — Memory Store
Build a semantic memory store for BARKEEP: scored recall, per-patron
namespacing, supersede on contradiction, soft-delete on request.

Run:  python start.py
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
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
    """Embed one string with EMBED_MODEL.

    Returns the embedding vector as a list of floats.
    """
    # TODO: call client.embeddings.create(model=EMBED_MODEL, input=[text])
    #       and return response.data[0].embedding
    raise NotImplementedError("TODO")


def normalise(similarities: list[float]) -> list[float]:
    """Spread raw similarities across [0, 1] within the candidate set.

    Cosine similarity between short sentences lands in a narrow band (0.03 to
    0.38 is typical), so blending it raw against a recency term that spans
    0 to 1 lets recency decide every ranking. Min-max fixes that.
    """
    # TODO: return [] for an empty list
    #       find low and high; if they are equal (within 1e-9), return 1.0 for each
    #       otherwise return (s - low) / (high - low) for each s
    raise NotImplementedError("TODO")


def recency_weight(written_at: float, now: float | None = None) -> float:
    """Decay as a weight: a memory counts for half as much per half-life."""
    now = now if now is not None else time.time()
    # TODO: age_days = (now - written_at) / DAY_SECONDS, floored at 0
    #       return 0.5 ** (age_days / HALF_LIFE_DAYS)
    raise NotImplementedError("TODO")


def score_memory(
    relevance: float, written_at: float, importance: float, now: float | None = None
) -> tuple[float, float]:
    """Return (recency, combined score) for one candidate."""
    # TODO: recency = recency_weight(written_at, now)
    #       combined = RELEVANCE_WEIGHT * relevance
    #                + RECENCY_WEIGHT * recency
    #                + IMPORTANCE_WEIGHT * importance
    #       return (recency, combined)
    raise NotImplementedError("TODO")


def build_collection(path: str = ".chroma_memories"):
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
        """Write one memory and return its id."""
        memory_id = str(uuid.uuid4())  # noqa: F841 — you return this at the end
        # TODO: call self.collection.add with
        #         ids=[memory_id]
        #         embeddings=[embed(text, self.client)]
        #         documents=[text]
        #         metadatas=[{...}] holding patron, kind, importance,
        #           written_at (default to time.time()), active=True,
        #           and superseded_by=""
        #       Chroma metadata values must be str, int, float, or bool —
        #       that is why superseded_by is "" rather than None.
        #       Then return memory_id.
        raise NotImplementedError("TODO")

    def recall(self, query: str, *, patron: str, k: int = 5) -> list[ScoredMemory]:
        """Return the k memories most worth putting in the next prompt."""
        # TODO: 1. query the collection:
        #            query_embeddings=[embed(query, self.client)]
        #            n_results=max(k * 4, k)        # over-fetch, then rescore
        #            where={"$and": [{"patron": {"$eq": patron}},
        #                            {"active": {"$eq": True}}]}
        #       2. return [] if results["ids"] is empty or results["ids"][0] is empty
        #       3. similarities = [1.0 - d for d in results["distances"][0]]
        #          relevances = normalise(similarities)
        #       4. for each (id, document, metadata, relevance), call score_memory
        #          and build a ScoredMemory
        #       5. sort by score descending and return the first k
        raise NotImplementedError("TODO")

    def all_active(self, *, patron: str) -> list[dict]:
        """Every live memory for one patron, newest first."""
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
        """Flip a memory's active flag off, keeping the row."""
        # TODO: 1. existing = self.collection.get(ids=[memory_id])
        #       2. return False if existing["ids"] is empty
        #       3. copy existing["metadatas"][0], set active=False and
        #          superseded_by, then self.collection.update(ids=..., metadatas=...)
        #       4. return True
        raise NotImplementedError("TODO")

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
    """Decide whether a new fact is stored, replaces an existing one, or is a duplicate.

    Provided for you — the interesting part is what you do with the answer.
    """
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
    # TODO: call client.responses.parse with
    #         model=MODEL, reasoning={"effort": "none"}, text_format=WriteDecision
    #         input=[{"role": "system", "content": WRITE_PROMPT},
    #                {"role": "user", "content": f"Patron: {patron}\nThey said: {user_input}"}]
    #       return response.output_parsed.candidates, or [] if nothing parsed
    raise NotImplementedError("TODO")


def write_memories(
    user_input: str, store: MemoryStore, patron: str, client: OpenAI
) -> list[str]:
    """Extract candidates, then store, replace, or skip each one."""
    # TODO: for each candidate from propose_memories(...):
    #         1. neighbours = store.recall(candidate.text, patron=patron, k=3)
    #            A contradiction or a duplicate is always semantically close,
    #            so the neighbours are where it will be.
    #         2. decision = resolve(candidate.text, neighbours, client)
    #         3. if decision.action == "skip": print a note and move on —
    #            storing it again would only duplicate
    #         4. otherwise store it with store.remember(...)
    #         5. if decision.action == "replace": supersede
    #            neighbours[decision.target].memory_id with the new id
    #       return the list of ids actually written
    raise NotImplementedError("TODO")


def build_system_prompt(memories: list[ScoredMemory]) -> str:
    """The persona, plus whatever recall selected for this turn."""
    # TODO: return PERSONA alone (plus a note that the patron is new) when
    #       memories is empty; otherwise append a bulleted block of memory text
    raise NotImplementedError("TODO")


def chat(
    user_input: str,
    thread: list[dict],
    store: MemoryStore,
    patron: str,
    client: OpenAI,
) -> str:
    """One turn: recall, answer, then write anything durable."""
    # TODO: 1. memories = store.recall(user_input, patron=patron, k=5)
    #       2. append the user message to thread
    #       3. call client.responses.create with
    #            input=[{"role": "system", "content": build_system_prompt(memories)}, *thread]
    #       4. append the assistant reply to thread
    #       5. call write_memories(...) — the hot-path write
    #       6. return the reply text
    raise NotImplementedError("TODO")


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
