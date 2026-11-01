"""
Module 9 Demo — Multi-Agent Systems
Run:  python module-09-multi-agent/demo/demo.py

  Part 1: Route one question to one specialist
  Part 2: A critic can send the draft back
  Part 3: Two agents debate, a judge rules
  Part 4: Three specialists vote
  Part 5: Swarm handoffs

Requires: OPENAI_API_KEY environment variable.
"""

from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

demo_route = import_module("01_route").demo_route
demo_critic = import_module("02_critic").demo_critic
demo_debate = import_module("03_debate").demo_debate
demo_consensus = import_module("04_consensus").demo_consensus
demo_swarm = import_module("05_swarm").demo_swarm

DEMOS = {
    "1": ("Route one question", demo_route),
    "2": ("Supervisor-critic", demo_critic),
    "3": ("Debate", demo_debate),
    "4": ("Consensus", demo_consensus),
    "5": ("Swarm", demo_swarm),
}


def main():
    load_dotenv()
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 9 DEMO — MULTI-AGENT")
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
    print("  1. Route      — one classifier, one specialist")
    print("  2. Critic     — a reviewer can reject and demand a revision")
    print("  3. Debate     — two sides, then a judge")
    print("  4. Consensus  — independent votes, then a tally")
    print("  5. Swarm      — agents hand off, each with scoped tools")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
