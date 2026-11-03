"""A semantic memory store: write facts, select them back by meaning.

Memories live in a Chroma collection, one namespace per patron. Recall embeds
the current turn, over-fetches from the index, then ranks on relevance,
recency, and importance.
"""

import time
import uuid
from dataclasses import dataclass

import chromadb
from openai import OpenAI

EMBED_MODEL = "text-embedding-3-small"

# How long before a memory counts for half as much in the ranking. Decay is a
# weight here, not a delete.
HALF_LIFE_DAYS = 30.0

RELEVANCE_WEIGHT = 0.6
RECENCY_WEIGHT = 0.25
IMPORTANCE_WEIGHT = 0.15

DAY_SECONDS = 86_400


def embed(text: str, client: OpenAI) -> list[float]:
    """Embed one string with the same model Module 5 used."""
    response = client.embeddings.create(model=EMBED_MODEL, input=[text])
    return response.data[0].embedding


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

    @property
    def age_days(self) -> float:
        return (time.time() - self.written_at) / DAY_SECONDS


def normalise(similarities: list[float]) -> list[float]:
    """Spread raw similarities across [0, 1] within the candidate set.

    Cosine similarity between two short sentences lands in a narrow band —
    0.03 to 0.38 is typical — so blending it directly against recency lets
    recency win every time. Normalising within the candidates you actually
    retrieved makes the weights below mean what they say.
    """
    if not similarities:
        return []
    low, high = min(similarities), max(similarities)
    if high - low < 1e-9:
        return [1.0] * len(similarities)
    return [(s - low) / (high - low) for s in similarities]


def recency_weight(written_at: float) -> float:
    """Decay as a weight: a memory counts for half as much per half-life."""
    age_days = max(0.0, (time.time() - written_at) / DAY_SECONDS)
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def score_memory(relevance: float, written_at: float, importance: float) -> tuple[float, float]:
    """Return (recency, combined score) for one candidate."""
    recency = recency_weight(written_at)
    combined = (
        RELEVANCE_WEIGHT * relevance
        + RECENCY_WEIGHT * recency
        + IMPORTANCE_WEIGHT * importance
    )
    return recency, combined


class MemoryStore:
    """Semantic memory over a Chroma collection.

    Pass ``collection`` to reuse an existing one; the default builds an
    in-process collection so the demos leave nothing behind on disk.
    """

    def __init__(self, client: OpenAI, collection=None, name: str = "cantina_memories"):
        self.client = client
        self.collection = collection or chromadb.EphemeralClient().get_or_create_collection(
            name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def remember(
        self,
        text: str,
        *,
        patron: str,
        kind: str = "preference",
        importance: float = 1.0,
        written_at: float | None = None,
        key: str = "",
    ) -> str:
        """Write one memory and return its id.

        ``key`` is the old-fashioned topic label. Nothing in recall uses it —
        it exists so Part 2 can show keyed lookup failing on the same data.
        """
        memory_id = str(uuid.uuid4())
        self.collection.add(
            ids=[memory_id],
            embeddings=[embed(text, self.client)],
            documents=[text],
            metadatas=[
                {
                    "patron": patron,
                    "kind": kind,
                    "key": key,
                    "importance": importance,
                    "written_at": written_at if written_at is not None else time.time(),
                    "active": True,
                    "superseded_by": "",
                }
            ],
        )
        return memory_id

    def recall(self, query: str, *, patron: str, k: int = 5) -> list[ScoredMemory]:
        """Return the k memories most worth putting in the next prompt."""
        results = self.collection.query(
            query_embeddings=[embed(query, self.client)],
            n_results=max(k * 4, k),
            where={"$and": [{"patron": {"$eq": patron}}, {"active": {"$eq": True}}]},
        )
        if not results["ids"] or not results["ids"][0]:
            return []

        # Chroma's cosine distance is 1 - similarity for unit-length embeddings.
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

        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:k]

    def all_active(self, *, patron: str) -> list[dict]:
        """Every live memory for one patron, newest first. For inspection."""
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
        """Retire a memory that a newer one replaces, keeping the trail."""
        return self._deactivate(memory_id, superseded_by=by)

    def forget(self, memory_id: str) -> bool:
        """Soft-delete on request: the content stops reaching the model.

        The row survives so you can prove something was removed without
        retaining what it said.
        """
        return self._deactivate(memory_id)

    def prefix_recall(self, prefix: str, *, patron: str) -> list[dict]:
        """Keyed lookup, kept only so Part 2 can show it failing."""
        return [
            row
            for row in self.all_active(patron=patron)
            if row.get("key", "").lower().startswith(prefix.lower())
        ]
