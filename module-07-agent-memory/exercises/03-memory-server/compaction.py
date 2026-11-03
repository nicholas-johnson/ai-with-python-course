"""
Compaction, carried forward from Exercise 02.

Budget-triggered compaction that preserves decisions, open tasks, and
constraints, and never separates a tool call from its output.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
ENCODING = tiktoken.get_encoding("o200k_base")
MESSAGE_OVERHEAD = 4

BUDGET_TOKENS = 1200
KEEP_RECENT = 4




class Anchor(BaseModel):
    kind: Literal["decision", "open_task", "constraint"]
    text: str


class Compaction(BaseModel):
    summary: str = Field(description="What was discussed, in at most 70 words")
    anchors: list[Anchor] = Field(
        description="Decisions made, tasks left open, and constraints stated"
    )


@dataclass
class CompactionReport:
    tokens_before: int
    tokens_after: int
    messages_compacted: int
    anchors: list[Anchor]
    requested_split: int
    actual_split: int


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


def count_tokens(messages: list[dict]) -> int:
    """Approximate the prompt cost of a message list.

    Handles Responses API items as well as chat messages, so a function call
    and its output are counted rather than skipped.
    """
    total = 0
    for message in messages:
        parts = [
            str(message.get("content") or ""),
            str(message.get("arguments") or ""),
            str(message.get("output") or ""),
            str(message.get("name") or ""),
        ]
        total += len(ENCODING.encode(" ".join(p for p in parts if p))) + MESSAGE_OVERHEAD
    return total


def safe_split(messages: list[dict], index: int) -> int:
    """Move a split boundary back until it does not break a tool pair."""
    index = max(0, min(index, len(messages)))
    while 0 < index < len(messages) and messages[index].get("type") == "function_call_output":
        index -= 1
    return index


def summarise(messages: list[dict], client: OpenAI) -> Compaction:
    """Summarise a span into a summary plus anchors."""
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
    return response.output_parsed or Compaction(summary="(summary unavailable)", anchors=[])


def render_block(result: Compaction, carried: list[Anchor] | None = None) -> str:
    """Render a compaction into the single system message that replaces a span.

    Anchors from an earlier compaction are re-emitted verbatim, which is what
    stops detail draining away pass after pass.
    """
    anchors = list(carried or []) + list(result.anchors)
    lines = [f"[Earlier conversation] {result.summary}"]
    for label, kind in (
        ("Decisions", "decision"),
        ("Open tasks", "open_task"),
        ("Constraints", "constraint"),
    ):
        matching = [anchor.text for anchor in anchors if anchor.kind == kind]
        if matching:
            lines.append(f"{label}: " + "; ".join(matching))
    return "\n".join(lines)


def compact(
    messages: list[dict],
    *,
    budget_tokens: int,
    keep_recent: int,
    client: OpenAI,
    carried: list[Anchor] | None = None,
) -> tuple[list[dict], CompactionReport | None]:
    """Bring a thread under budget, preserving the anchors inside it."""
    tokens_before = count_tokens(messages)
    if tokens_before <= budget_tokens or len(messages) <= keep_recent:
        return messages, None

    requested_split = max(1, len(messages) - keep_recent)
    actual_split = safe_split(messages, requested_split)
    if actual_split == 0:
        return messages, None

    old, recent = messages[:actual_split], messages[actual_split:]
    result = summarise(old, client)
    block = {"role": "system", "content": render_block(result, carried)}
    compacted = [block, *recent]

    report = CompactionReport(
        tokens_before=tokens_before,
        tokens_after=count_tokens(compacted),
        messages_compacted=len(old),
        anchors=result.anchors,
        requested_split=requested_split,
        actual_split=actual_split,
    )
    return compacted, report
