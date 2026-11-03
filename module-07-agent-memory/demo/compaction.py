"""Compaction: replace a span of history with a summary that keeps the anchors.

The anchors are the parts a summary tends to lose and an agent cannot do
without: decisions already made, tasks still open, constraints to respect.
"""

import os
from dataclasses import dataclass
from typing import Literal

from budget import count_messages
from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


class Anchor(BaseModel):
    kind: Literal["decision", "open_task", "constraint"]
    text: str


class Compaction(BaseModel):
    summary: str = Field(description="What was discussed, in under 120 words")
    anchors: list[Anchor] = Field(
        description="Every decision made, task left open, and constraint stated"
    )


@dataclass
class CompactionReport:
    tokens_before: int
    tokens_after: int
    messages_compacted: int
    anchors: list[Anchor]
    requested_split: int
    actual_split: int

    @property
    def split_moved(self) -> bool:
        return self.requested_split != self.actual_split


COMPACT_PROMPT = """Compact this stretch of conversation.

Write a summary of at most 70 words, then list the anchors. An anchor is
something a reader would have to know to carry the conversation on:
  decision   - something settled, with the outcome
  open_task  - something still outstanding
  constraint - a limit or rule to respect

Rules for anchors: at most five, each one short clause under fifteen words, no
duplication of the summary. Keep names, numbers, and identifiers exact.

The whole point is to be smaller than what it replaces. Anything that is
merely conversation does not survive."""


def safe_split(messages: list[dict], index: int) -> int:
    """Move a split boundary back until it does not break a tool pair.

    A ``function_call`` and its ``function_call_output`` have to travel
    together or the API rejects the request, so the boundary can never fall
    between them.
    """
    index = max(0, min(index, len(messages)))
    while index > 0 and messages[index].get("type") == "function_call_output":
        index -= 1
    return index


def summarise(messages: list[dict], client: OpenAI | None) -> Compaction:
    """Summarise a span into a summary plus anchors."""
    if client is None:
        return _stub_compaction(messages)

    transcript = "\n".join(
        f"{m.get('role') or m.get('type', 'item')}: "
        f"{m.get('content') or m.get('output') or m.get('arguments') or ''}"
        for m in messages
    )
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Compaction,
        input=[
            {"role": "system", "content": COMPACT_PROMPT},
            {"role": "user", "content": transcript},
        ],
    )
    return response.output_parsed or _stub_compaction(messages)


def _stub_compaction(messages: list[dict]) -> Compaction:
    """Fallback so the compaction demo still runs without an API key."""
    return Compaction(
        summary=(
            f"[stub summary — no API key] {len(messages)} earlier messages covering "
            "the patron's order, their tab, and the station's docking schedule."
        ),
        anchors=[
            Anchor(kind="decision", text="Charge everything to the ship's account"),
            Anchor(kind="open_task", text="Marek still owes 12 credits on his tab"),
            Anchor(kind="constraint", text="No synthcitrus in anything served to Tanaka"),
        ],
    )


def render_block(result: Compaction, carried: list[Anchor] | None = None) -> str:
    """Render a compaction into the single system message that replaces a span.

    ``carried`` holds anchors from an earlier compaction. Re-emitting them
    verbatim is what stops detail draining away pass after pass.
    """
    anchors = list(carried or []) + list(result.anchors)
    lines = [f"[Earlier conversation] {result.summary}"]
    for label, kind in (
        ("Decisions", "decision"),
        ("Open tasks", "open_task"),
        ("Constraints", "constraint"),
    ):
        matching = [a.text for a in anchors if a.kind == kind]
        if matching:
            lines.append(f"{label}: " + "; ".join(matching))
    return "\n".join(lines)


def compact(
    messages: list[dict],
    *,
    budget_tokens: int,
    keep_recent: int = 6,
    keep_leading: int = 1,
    client: OpenAI | None = None,
    carried: list[Anchor] | None = None,
) -> tuple[list[dict], CompactionReport | None]:
    """Bring a message list under budget, preserving the anchors inside it.

    The first ``keep_leading`` messages — the system prompt and anything else
    assembled fresh each turn — are left byte-identical so the prompt cache
    prefix survives. The compaction block is inserted directly after them.
    """
    tokens_before = count_messages(messages)
    if tokens_before <= budget_tokens or len(messages) <= keep_leading + keep_recent:
        return messages, None

    preamble, rest = messages[:keep_leading], messages[keep_leading:]
    requested_split = max(1, len(rest) - keep_recent)
    actual_split = safe_split(rest, requested_split)
    if actual_split == 0:
        return messages, None

    old, recent = rest[:actual_split], rest[actual_split:]
    result = summarise(old, client)
    block = {"role": "system", "content": render_block(result, carried)}
    compacted = [*preamble, block, *recent]

    report = CompactionReport(
        tokens_before=tokens_before,
        tokens_after=count_messages(compacted),
        messages_compacted=len(old),
        anchors=result.anchors,
        requested_split=requested_split,
        actual_split=actual_split,
    )
    return compacted, report


def truncate(messages: list[dict], *, budget_tokens: int, keep_leading: int = 1) -> list[dict]:
    """The naive alternative: drop the oldest messages until it fits.

    Kept so Parts 1 and 4 can show what it throws away.
    """
    preamble, rest = messages[:keep_leading], list(messages[keep_leading:])
    while rest and count_messages([*preamble, *rest]) > budget_tokens:
        rest.pop(0)
    return [*preamble, *rest]
