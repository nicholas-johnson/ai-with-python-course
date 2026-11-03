"""
Module 7 Demo — Agent Memory and Context Engineering
Run:  python module-07-agent-memory/demo/demo.py

  Part 1: The context budget — where the tokens go, and what truncation destroys
  Part 2: Semantic memory — scored recall, next to keyed lookup failing
  Part 3: The memory writer — what to write, and what a new fact replaces
  Part 4: Compaction — anchors preserved under a token budget
  Part 5: Memory agent — recall, write, and compact in one chat

Requires: OPENAI_API_KEY for Parts 2, 3, and 5, and the rag extra for ChromaDB.
Parts 1 and 4 run without a key (Part 4 falls back to a stub summariser).
"""

import os
from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

demo_context_budget = import_module("01_context_budget").demo_context_budget
demo_semantic_memory = import_module("02_semantic_memory").demo_semantic_memory
demo_memory_writer = import_module("03_memory_writer").demo_memory_writer
demo_compaction = import_module("04_compaction").demo_compaction
demo_memory_agent = import_module("05_memory_agent").demo_memory_agent

# Parts that work with no API key at all.
OFFLINE = {"1", "4"}

DEMOS = {
    "1": ("The context budget", demo_context_budget),
    "2": ("Semantic memory", demo_semantic_memory),
    "3": ("The memory writer", demo_memory_writer),
    "4": ("Compaction", demo_compaction),
    "5": ("Memory agent", demo_memory_agent),
}


def main():
    load_dotenv()
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    client = OpenAI() if has_key else None

    print("\n" + "=" * 60)
    print("  MODULE 7 DEMO — AGENT MEMORY AND CONTEXT ENGINEERING")
    print("=" * 60)
    if not has_key:
        print("\n  No OPENAI_API_KEY — Parts 1 and 4 only.")

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            suffix = "" if has_key or key in OFFLINE else "  (needs an API key)"
            print(f"  {key}. {label}{suffix}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            if client is None and choice not in OFFLINE:
                print("\nThat part needs OPENAI_API_KEY set in .env")
                continue
            _, fn = DEMOS[choice]
            print()
            fn(client)
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. Context budget  — history is the only component with no ceiling")
    print("  2. Semantic memory — recall on meaning, scored on relevance, recency, importance")
    print("  3. Memory writer   — most turns hold nothing; a new fact supersedes the old one")
    print("  4. Compaction      — keep the decisions, keep the tool pairs, keep the cache prefix")
    print("  5. Memory agent    — all three moves, one chat loop")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
