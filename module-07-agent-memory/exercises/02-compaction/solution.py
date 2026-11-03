"""
Exercise 02 — Compaction (solution)
Keep a long conversation under a token budget without losing the decisions
inside it. Compaction, not truncation.

Run:  python solution.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

import tiktoken
from dotenv import load_dotenv
from memory_store import MemoryStore, build_collection
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
ENCODING = tiktoken.get_encoding("o200k_base")
MESSAGE_OVERHEAD = 4

BUDGET_TOKENS = 220
KEEP_RECENT = 2
PATRON = "zara"

PERSONA = (
    "You are BARKEEP, the AI bartender at The Nebula's Edge cantina on Relay "
    "Station Omicron. You are warm, slightly wry, and you honour what a patron "
    "has already agreed with you earlier in the evening."
)

# A canned stretch of evening, loaded by /seed so compaction has something to
# chew on without typing twenty turns. The tool call sits at the end on purpose.
SAMPLE_THREAD = [
    {"role": "user", "content": "Evening. Set up a round for the Pathfinder crew."},
    {"role": "assistant", "content": "Six of them? Coming up."},
    {
        "role": "user",
        "content": (
            "Six, and charge the whole evening to the ship's account — I have standing "
            "authority, so do not chase anyone individually for credits."
        ),
    },
    {
        "role": "assistant",
        "content": "Noted: the evening goes to the Pathfinder account, nobody chased individually.",
    },
    {"role": "user", "content": "Tanaka is with us, so watch the synthcitrus."},
    {
        "role": "assistant",
        "content": (
            "Nothing citrus-derived goes near the Chief. The Void Mule is clean "
            "if they want sharp."
        ),
    },
    {"role": "user", "content": "How was the Veil run for the other crews?"},
    {
        "role": "assistant",
        "content": (
            "Loud. The Meridian crew came in arguing about sensor calibration and they "
            "have not stopped. The Horizon lot went quiet after the second round."
        ),
    },
    {"role": "user", "content": "And Marek still owes you, does he not?"},
    {
        "role": "assistant",
        "content": (
            "Twelve credits since the last rotation — under the fifty-credit "
            "clearance threshold."
        ),
    },
    {"role": "user", "content": "Add it to tonight's account. How much Comet Tail is left?"},
    {
        "type": "function_call",
        "name": "check_stock",
        "call_id": "call_stock_01",
        "arguments": '{"drink": "Comet Tail"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_stock_01",
        "output": '{"drink": "Comet Tail", "units_remaining": 11, "restock_eta_days": 2}',
    },
    {
        "role": "assistant",
        "content": "Eleven units, restock due in two days. Plenty for six.",
    },
]


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


def build_system_prompt(memories: list) -> str:
    """Persona plus whatever recall selected for this turn."""
    if not memories:
        return PERSONA
    block = "\n".join(f"- {memory.text}" for memory in memories)
    return PERSONA + f"\n\nWhat you remember about this patron:\n{block}"


def chat(
    user_input: str,
    thread: list[dict],
    carried: list[Anchor],
    store: MemoryStore,
    client: OpenAI,
) -> str:
    """One turn: recall, compact if over budget, answer."""
    memories = store.recall(user_input, patron=PATRON, k=5)
    thread.append({"role": "user", "content": user_input})

    compacted, report = compact(
        thread,
        budget_tokens=BUDGET_TOKENS,
        keep_recent=KEEP_RECENT,
        client=client,
        carried=carried,
    )
    if report:
        thread[:] = compacted
        carried.extend(report.anchors)
        print(
            f"  [auto-compacted {report.messages_compacted} messages, "
            f"{report.tokens_before} -> {report.tokens_after} tokens]"
        )

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[{"role": "system", "content": build_system_prompt(memories)}, *thread],
    )
    reply = response.output_text
    thread.append({"role": "assistant", "content": reply})
    return reply


def main():
    client = OpenAI()
    store = MemoryStore(client, build_collection())
    thread: list[dict] = []
    carried: list[Anchor] = []

    print("=== The Nebula's Edge — BARKEEP (compacting) ===")
    print(f"Budget: {BUDGET_TOKENS} tokens, keeping the last {KEEP_RECENT} messages verbatim")
    print("Commands: /budget, /anchors, /thread, /seed, /compact, quit\n")

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

        if user_input == "/budget":
            print(
                f"[{count_tokens(thread)} tokens in {len(thread)} messages "
                f"/ budget {BUDGET_TOKENS}]\n"
            )
            continue

        if user_input == "/anchors":
            if not carried:
                print("[No anchors yet — nothing has been compacted]\n")
            else:
                for anchor in carried:
                    print(f"  [{anchor.kind}] {anchor.text}")
                print()
            continue

        if user_input == "/thread":
            for index, message in enumerate(thread):
                kind = message.get("type") or message.get("role")
                body = message.get("content") or message.get("arguments") or message.get("output")
                print(f"  {index:>2}. {kind:<22} {str(body)[:54]}")
            print()
            continue

        if user_input == "/seed":
            thread.extend(SAMPLE_THREAD)
            print(f"[Loaded {len(SAMPLE_THREAD)} messages — {count_tokens(thread)} tokens]\n")
            continue

        if user_input == "/compact":
            compacted, report = compact(
                thread, budget_tokens=0, keep_recent=KEEP_RECENT, client=client, carried=carried
            )
            if not report:
                print("[Nothing to compact yet]\n")
                continue
            thread[:] = compacted
            carried.extend(report.anchors)
            print(
                f"[Compacted {report.messages_compacted} messages, "
                f"{report.tokens_before} -> {report.tokens_after} tokens]"
            )
            if report.actual_split != report.requested_split:
                print(
                    f"[Boundary moved from {report.requested_split} to "
                    f"{report.actual_split} to keep a tool pair together]"
                )
            print()
            continue

        print(f"Agent: {chat(user_input, thread, carried, store, client)}\n")


if __name__ == "__main__":
    main()
