"""Part 1: Where the context budget goes, and what truncation destroys.
No model call.
Run alone:  python module-07-agent-memory/demo/01_context_budget.py
"""

import json

from budget import bar, count_messages, count_text
from compaction import truncate
from sample_prompt import (
    HISTORY,
    MEMORIES,
    RETRIEVED_DOCS,
    SYSTEM_PROMPT,
    TOOL_SCHEMAS,
    assemble,
)

BUDGET = 540

# The system prompt, the memory block, and the retrieved docs are assembled
# fresh every turn, so truncation only has the history to work with.
PREAMBLE_MESSAGES = 3


def component_tokens() -> list[tuple[str, int]]:
    """Measure each component of the prompt separately."""
    return [
        ("System prompt", count_text(SYSTEM_PROMPT["content"])),
        ("Tool schemas", count_text(json.dumps(TOOL_SCHEMAS))),
        ("Retrieved docs", count_text("\n\n".join(RETRIEVED_DOCS))),
        ("Memories", count_text("\n".join(MEMORIES))),
        ("History", count_messages(HISTORY)),
    ]


def demo_context_budget(client=None):
    print("=" * 60)
    print("PART 1: THE CONTEXT BUDGET")
    print("=" * 60)
    print()

    components = component_tokens()
    total = sum(tokens for _, tokens in components)

    print(f"  One turn of a working agent — {total} tokens:\n")
    for label, tokens in components:
        print(f"    {label:<16} {tokens:>5}  {bar(tokens, total)}  {tokens / total:>4.0%}")

    print()
    print("  Every one of these is resent on every call. Only one of them grows")
    print("  without limit: history. Turn 50 resends turns 1 through 49.")
    print("  (Tool schemas travel in the tools parameter, not the message list,")
    print("   but the model pays for them exactly the same.)\n")

    print("-" * 60)
    print(f"  Now hold it to a {BUDGET}-token budget by dropping the oldest messages.")
    print("-" * 60)
    print()

    full = assemble()
    truncated = truncate(full, budget_tokens=BUDGET, keep_leading=PREAMBLE_MESSAGES)
    dropped = full[PREAMBLE_MESSAGES : PREAMBLE_MESSAGES + (len(full) - len(truncated))]

    print(f"  Before: {count_messages(full)} tokens, {len(full)} messages")
    print(f"  After:  {count_messages(truncated)} tokens, {len(truncated)} messages")
    print(f"  Dropped the {len(dropped)} oldest messages. Here is one of them:\n")

    for message in dropped:
        if message.get("role") == "user" and "ship's account" in message.get("content", ""):
            print(f"    {message['role']}: {message['content']}")
            break

    print()
    print("  That was the decision. The agent will now start chasing the Pathfinder")
    print("  crew for credits individually, because as far as it can see, nobody")
    print("  ever told it not to.")
    print()
    print("  Truncation is cheap and it loses exactly the wrong thing. Part 4")
    print("  compacts the same thread instead.")
    print()


if __name__ == "__main__":
    demo_context_budget()
