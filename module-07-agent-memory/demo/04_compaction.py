"""Part 4: Compaction under a token budget, next to naive truncation.
Runs without an API key — the summariser falls back to a stub.
Run alone:  python module-07-agent-memory/demo/04_compaction.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

from budget import count_messages
from compaction import compact, safe_split, truncate
from sample_prompt import HISTORY, assemble

load_dotenv()

BUDGET = 560
KEEP_RECENT = 3
PREAMBLE_MESSAGES = 3


def describe(message: dict) -> str:
    kind = message.get("type") or message.get("role")
    body = message.get("content") or message.get("arguments") or message.get("output") or ""
    return f"{kind:<22} {str(body)[:48]}"


def demo_compaction(client: OpenAI | None = None):
    if client is None and os.getenv("OPENAI_API_KEY"):
        client = OpenAI()

    print("=" * 60)
    print("PART 4: COMPACTION")
    print("=" * 60)
    print()
    if client is None:
        print("  No OPENAI_API_KEY — using a stub summariser. The mechanics are real.\n")

    full = assemble()
    print(f"  Thread: {len(full)} messages, {count_messages(full)} tokens")
    print(f"  Budget: {BUDGET} tokens, keeping the last {KEEP_RECENT} messages verbatim\n")

    print("-" * 60)
    print("  First, the split boundary")
    print("-" * 60)
    print()

    rest = full[PREAMBLE_MESSAGES:]
    requested = len(rest) - KEEP_RECENT
    actual = safe_split(rest, requested)
    print(f"  Wanted to split at index {requested}: {describe(rest[requested])}")
    if actual != requested:
        print(f"  That is a tool output — its call sits at index {requested - 1}.")
        print(f"  safe_split moved the boundary back to {actual}: {describe(rest[actual])}")
        print("  Split them and the API rejects the request.")
    else:
        print("  Safe as it stands — no tool pair straddles the boundary.")
    print()

    compacted, report = compact(
        full,
        budget_tokens=BUDGET,
        keep_recent=KEEP_RECENT,
        keep_leading=PREAMBLE_MESSAGES,
        client=client,
    )

    print("-" * 60)
    print("  Compaction")
    print("-" * 60)
    print()
    print(f"  {report.messages_compacted} messages -> one block")
    print(f"  {report.tokens_before} tokens -> {report.tokens_after} tokens "
          f"({1 - report.tokens_after / report.tokens_before:.0%} smaller)")
    print(f"  Anchors kept: {len(report.anchors)}\n")

    for anchor in report.anchors:
        print(f"    [{anchor.kind}] {anchor.text}")
    print()

    print("  The block that replaced them:\n")
    for line in compacted[PREAMBLE_MESSAGES]["content"].splitlines():
        print(f"    {line}")
    print()

    print("-" * 60)
    print("  The same thread, truncated to the same budget")
    print("-" * 60)
    print()

    truncated = truncate(full, budget_tokens=BUDGET, keep_leading=PREAMBLE_MESSAGES)
    survived = {str(m.get("content", "")) for m in truncated}
    lost = [
        m for m in HISTORY
        if m.get("content") and str(m["content"]) not in survived
    ]

    print(f"  {count_messages(truncated)} tokens, same ballpark. What it cost:\n")
    for message in lost:
        print(f"    lost  {message.get('role')}: {str(message['content'])[:62]}...")

    print()
    print("  Compaction kept the decision about the ship's account as an anchor.")
    print("  Truncation threw the turn away. Both fit the budget; only one of")
    print("  them still knows what was agreed.")
    print()
    print("  The system prompt is untouched in both cases — rewrite index 0 and")
    print("  you lose the prompt cache prefix on every later call.")
    print()


if __name__ == "__main__":
    demo_compaction()
