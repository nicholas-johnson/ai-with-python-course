"""
Module 7 Demo — Agent Memory
Run:  python module-07-agent-memory/demo/demo.py

  Part 1: Session memory — a capped message list
  Part 2: Long-term memory — importance decay
  Part 3: Summarise a long conversation
  Part 4: An agent that writes memories as you talk

Requires: OPENAI_API_KEY for Parts 3 and 4.
"""

from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

demo_session_memory = import_module("01_session_memory").demo_session_memory
demo_long_term_memory = import_module("02_long_term_memory").demo_long_term_memory
demo_summarise = import_module("03_summarise").demo_summarise
demo_memory_agent = import_module("04_memory_agent").demo_memory_agent

DEMOS = {
    "1": ("Session memory", demo_session_memory),
    "2": ("Long-term memory", demo_long_term_memory),
    "3": ("Summarise", demo_summarise),
    "4": ("Memory-enhanced agent", demo_memory_agent),
}


def main():
    load_dotenv()
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 7 DEMO — AGENT MEMORY")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn(client)
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. Session memory   — a capped list; the oldest turn falls off")
    print("  2. Long-term memory — keys with importance that decays")
    print("  3. Summarise        — compress old turns before they blow the window")
    print("  4. Memory agent     — the model decides what is worth keeping")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
