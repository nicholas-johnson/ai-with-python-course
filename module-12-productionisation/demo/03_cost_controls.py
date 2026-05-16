"""
Demo 03 — Cost Controls
=========================
Shows token budget tracking, model tiering, and cost awareness.

Run:  python module-12-productionisation/demo/03_cost_controls.py
"""

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


class CostTracker:
    COST_PER_1K = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
    }

    def __init__(self, session_budget: int = 5000, daily_budget: int = 100_000):
        self.session_usage = 0
        self.daily_usage = 0
        self.session_budget = session_budget
        self.daily_budget = daily_budget
        self.session_cost_usd = 0.0
        self.calls = 0

    def record(self, model: str, prompt_tokens: int, completion_tokens: int):
        total = prompt_tokens + completion_tokens
        self.session_usage += total
        self.daily_usage += total
        self.calls += 1
        rates = self.COST_PER_1K.get(model, self.COST_PER_1K["gpt-4o-mini"])
        self.session_cost_usd += (prompt_tokens / 1000) * rates["input"] + (completion_tokens / 1000) * rates["output"]

    def within_budget(self) -> bool:
        return self.session_usage < self.session_budget and self.daily_usage < self.daily_budget

    def summary(self) -> str:
        return (
            f"  Calls: {self.calls} | "
            f"Tokens: {self.session_usage:,}/{self.session_budget:,} session | "
            f"Est. cost: ${self.session_cost_usd:.4f}"
        )


def classify_complexity(query: str) -> str:
    simple_keywords = ["what", "who", "when", "define", "list"]
    return "simple" if any(kw in query.lower() for kw in simple_keywords) else "complex"


def demo_cost_controls():
    print("=" * 60)
    print("  DEMO: Cost Controls")
    print("=" * 60)

    tracker = CostTracker(session_budget=2000)
    queries = [
        "What is the capital of France?",
        "Explain the implications of quantum computing on modern cryptography and suggest three mitigation strategies.",
        "List three Italian dishes.",
        "Compare the economic policies of Keynesianism and monetarism with historical examples.",
        "Who wrote Hamlet?",
    ]

    for query in queries:
        if not tracker.within_budget():
            print(f"\n  BUDGET EXCEEDED — rejecting: {query[:50]}...")
            continue

        complexity = classify_complexity(query)
        model = "gpt-4o-mini" if complexity == "simple" else "gpt-4o"
        print(f"\n  Query: {query[:60]}...")
        print(f"  Complexity: {complexity} → Model: {model}")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}],
            max_tokens=150,
        )
        answer = response.choices[0].message.content.strip()
        tracker.record(model, response.usage.prompt_tokens, response.usage.completion_tokens)

        print(f"  Answer: {answer[:80]}...")
        print(f"  Tokens used: {response.usage.total_tokens} | {tracker.summary()}")

    print(f"\n--- Session summary ---")
    print(tracker.summary())
    print()


if __name__ == "__main__":
    demo_cost_controls()
