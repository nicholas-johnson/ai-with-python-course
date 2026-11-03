"""Deciding what to write, and what a new fact replaces.

Two structured calls. The first asks whether a turn contains anything worth
keeping; the second asks whether the new fact contradicts one already stored.
"""

import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from memory_store import MemoryStore

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


class ConflictDecision(BaseModel):
    conflicts_with: int = Field(
        description="Index of the existing memory the new fact replaces, or -1 for none"
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

CONFLICT_PROMPT = """A new fact about a patron has just been recorded.

Decide whether it replaces one of the existing memories listed. It replaces an
existing memory only when both cannot be true at once - a changed preference, a
lifted constraint, a settled debt. A fact that merely adds detail replaces
nothing. Answer with the index, or -1."""


def propose_memories(user_message: str, client: OpenAI, patron: str = "the patron") -> list[MemoryCandidate]:
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


def find_conflict(text: str, neighbours: list, client: OpenAI) -> int:
    """Return the index of the memory the new fact replaces, or -1."""
    if not neighbours:
        return -1

    listing = "\n".join(f"{i}: {m.text}" for i, m in enumerate(neighbours))
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=ConflictDecision,
        input=[
            {"role": "system", "content": CONFLICT_PROMPT},
            {"role": "user", "content": f"New fact: {text}\n\nExisting memories:\n{listing}"},
        ],
    )
    decision = response.output_parsed
    if not decision or not 0 <= decision.conflicts_with < len(neighbours):
        return -1
    return decision.conflicts_with


def write_candidates(
    candidates: list[MemoryCandidate],
    store: MemoryStore,
    *,
    patron: str,
    client: OpenAI,
    verbose: bool = False,
) -> list[str]:
    """Write candidates, superseding anything each one replaces."""
    written = []
    for candidate in candidates:
        # Recall the neighbours before writing: a conflict is always close by.
        neighbours = store.recall(candidate.text, patron=patron, k=3)
        memory_id = store.remember(
            candidate.text,
            patron=patron,
            kind=candidate.kind,
            importance=candidate.importance,
        )
        written.append(memory_id)

        index = find_conflict(candidate.text, neighbours, client)
        if index >= 0:
            store.supersede(neighbours[index].memory_id, by=memory_id)
            if verbose:
                print(f'    superseded: "{neighbours[index].text}"')
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
