"""Deciding what to write, and what a new fact replaces.

Two structured calls. The first asks whether a turn contains anything worth
keeping; the second asks whether the new fact contradicts one already stored.
"""

import os
from typing import Literal

from memory_store import MemoryStore
from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

MemoryKind = Literal["preference", "constraint", "identity", "commitment"]


class MemoryCandidate(BaseModel):
    text: str = Field(description="The fact, written as a standalone sentence")
    kind: MemoryKind
    importance: float = Field(ge=0.0, le=1.0, description="How much it should weigh in recall")


class WriteDecision(BaseModel):
    candidates: list[MemoryCandidate] = Field(
        description="Facts worth keeping. Empty when the turn holds nothing durable."
    )


class MergeDecision(BaseModel):
    action: Literal["store", "replace", "skip"]
    target: int = Field(
        default=-1, description="Index of the existing memory to replace, or -1"
    )
    reason: str = Field(description="One short sentence")


WRITE_PROMPT = """You decide what a bartender should remember about a patron.

Write a candidate only when the fact will still matter next week:
  preference  - a standing choice, e.g. a usual order
  constraint  - something that must always be respected, e.g. an allergy
  identity    - who the patron is, their role or ship
  commitment  - an open loop, e.g. an unpaid tab

Do not write one-off questions, transient state, chitchat, or anything a
database would already hold. Most turns produce no candidates at all.

Write each fact as a standalone sentence that makes sense months later with no
surrounding conversation, naming the patron rather than saying "the patron"."""

MERGE_PROMPT = """A new fact about a patron is about to be stored, alongside the
memories already held that are closest to it. Choose one action:

  replace - the new fact and an existing one cannot both be true: a changed
            preference, a lifted constraint, a settled debt. Give its index.
  skip    - an existing memory already says this, in equal or more detail.
            Storing it again would only duplicate. Give its index.
  store   - genuinely new, or it adds detail the existing memories lack.

Prefer skip over store when the difference is only phrasing."""


def propose_memories(
    user_message: str, client: OpenAI, patron: str = "the patron"
) -> list[MemoryCandidate]:
    """Ask the model what, if anything, this turn is worth remembering."""
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=WriteDecision,
        input=[
            {"role": "system", "content": WRITE_PROMPT},
            {"role": "user", "content": f"Patron: {patron}\nThey said: {user_message}"},
        ],
    )
    decision = response.output_parsed
    return decision.candidates if decision else []


def resolve(text: str, neighbours: list, client: OpenAI) -> MergeDecision:
    """Decide whether a new fact is stored, replaces an existing one, or is a duplicate."""
    if not neighbours:
        return MergeDecision(action="store", reason="Nothing stored nearby.")

    listing = "\n".join(f"{i}: {m.text}" for i, m in enumerate(neighbours))
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


def write_candidates(
    candidates: list[MemoryCandidate],
    store: MemoryStore,
    *,
    patron: str,
    client: OpenAI,
    verbose: bool = False,
) -> list[str]:
    """Write candidates, skipping duplicates and superseding what they replace."""
    written = []
    for candidate in candidates:
        # Recall the neighbours before writing: a conflict or a duplicate is
        # always semantically close to the new fact.
        neighbours = store.recall(candidate.text, patron=patron, k=3)
        decision = resolve(candidate.text, neighbours, client)

        if decision.action == "skip":
            if verbose:
                print(f'    skipped (already known): "{candidate.text}"')
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
            if verbose:
                print(f'    superseded: "{neighbours[decision.target].text}"')
        if verbose:
            print(f'    wrote [{candidate.kind}] "{candidate.text}"')

    return written


def write_turn(
    user_message: str,
    store: MemoryStore,
    *,
    patron: str,
    client: OpenAI,
    verbose: bool = False,
) -> list[str]:
    """Extract memories from one turn, superseding anything they replace.

    Returns the ids written. This runs on the hot path so the effect is
    visible; a chat product would do the same work after the response streams.
    """
    candidates = propose_memories(user_message, client, patron=patron)
    return write_candidates(candidates, store, patron=patron, client=client, verbose=verbose)
