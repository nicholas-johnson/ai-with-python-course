"""
Demo 03 — Cost Controls
=========================
Shows a token budget, model tiering, and running cost over a short session.

Needs OPENAI_API_KEY.

Run:  python module-12-productionisation/demo/03_cost_controls.py
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

CHEAP_MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
PREMIUM_MODEL = "gpt-6-sol"

SIMPLE_MARKERS = ("what", "who", "when", "where", "list", "define", "how many")


class CostTracker:
    # USD per 1K tokens, standard tier (October 2026)
    COST_PER_1K = {
        "gpt-6-luna": {"input": 0.0001, "output": 0.0005},
        "gpt-6-sol": {"input": 0.002, "output": 0.01},
    }

    def __init__(self, session_budget: int = 5_000, daily_budget: int = 100_000):
        self.session_budget = session_budget
        self.daily_budget = daily_budget
        self.session_tokens = 0
        self.daily_tokens = 0
        self.session_cost_usd = 0.0
        self.calls = 0

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.COST_PER_1K.get(model, self.COST_PER_1K[PREMIUM_MODEL])
        cost = (
            input_tokens / 1000 * rates["input"] + output_tokens / 1000 * rates["output"]
        )
        self.session_tokens += input_tokens + output_tokens
        self.daily_tokens += input_tokens + output_tokens
        self.session_cost_usd += cost
        self.calls += 1
        return cost

    def within_budget(self) -> bool:
        return (
            self.session_tokens < self.session_budget
            and self.daily_tokens < self.daily_budget
        )

    def summary(self) -> str:
        return (
            f"{self.calls} calls | "
            f"{self.session_tokens:,}/{self.session_budget:,} session tokens | "
            f"${self.session_cost_usd:.4f}"
        )


def classify_complexity(query: str) -> str:
    lowered = query.lower()
    return "simple" if any(marker in lowered for marker in SIMPLE_MARKERS) else "complex"


QUERIES = [
    "Who is the chief engineer of the Pathfinder?",
    "Compare the ion storm damage against the hull stress model and recommend a repair order.",
    "List three systems that draw power from the warp core.",
    "Explain the trade-off between diverting shield power to engines during a storm.",
    "What is the standard crew complement of a survey vessel?",
]


def demo_cost_controls():
    print("=" * 60)
    print("  DEMO: Cost Controls")
    print("=" * 60)
    print("\n  Lookups go to the cheap model, reasoning to the expensive one.")
    print("  The session budget is set low so it runs out partway through.\n")

    tracker = CostTracker(session_budget=2000)

    for query in QUERIES:
        if not tracker.within_budget():
            print(f"\n  refused (session budget spent): {query[:60]}...")
            continue

        complexity = classify_complexity(query)
        model = CHEAP_MODEL if complexity == "simple" else PREMIUM_MODEL

        print(f"\n  Query:  {query[:66]}")
        print(f"  Routed: {complexity} -> {model}")

        response = client.responses.create(
            model=model,
            reasoning={"effort": "none"},
            input=[{"role": "user", "content": query}],
            max_output_tokens=150,
        )
        cost = tracker.record(
            model, response.usage.input_tokens, response.usage.output_tokens
        )

        print(f"  Answer: {response.output_text.strip()[:66]}...")
        print(f"  Cost:   ${cost:.5f} for {response.usage.total_tokens} tokens")
        print(f"  Total:  {tracker.summary()}")

    print(f"\n--- Session summary ---\n  {tracker.summary()}")
    print("\n  Most of the spend sits in the few queries that needed the premium model.\n")


if __name__ == "__main__":
    demo_cost_controls()
