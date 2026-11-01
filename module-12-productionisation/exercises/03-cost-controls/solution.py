"""
Exercise 03 — Cost Controls (solution)

A budget that refuses work once it is spent, a router that sends easy
questions to a cheap model, and a cache that does not pay twice.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

CHEAP_MODEL = "gpt-6-luna"
PREMIUM_MODEL = "gpt-6-sol"

SIMPLE_MARKERS = ("what", "who", "when", "where", "list", "define", "how many")


# ---------------------------------------------------------------------------
# 1. Budget tracking
# ---------------------------------------------------------------------------


class CostTracker:
    """Tracks token usage against a session and a daily budget."""

    # USD per 1K tokens, standard tier (October 2026)
    COST_PER_1K = {
        "gpt-6-astra": {"input": 0.01, "output": 0.05},
        "gpt-6-sol": {"input": 0.002, "output": 0.01},
        "gpt-6-luna": {"input": 0.0001, "output": 0.0005},
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
            input_tokens / 1000 * rates["input"]
            + output_tokens / 1000 * rates["output"]
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
        """One-line usage report."""
        return (
            f"{self.calls} calls | "
            f"{self.session_tokens:,}/{self.session_budget:,} session tokens | "
            f"${self.session_cost_usd:.4f}"
        )


# ---------------------------------------------------------------------------
# 2. Model tiering
# ---------------------------------------------------------------------------


def classify_complexity(query: str) -> str:
    """Label a query "simple" (a lookup) or "complex" (needs reasoning)."""
    lowered = query.lower()
    return "simple" if any(marker in lowered for marker in SIMPLE_MARKERS) else "complex"


def choose_model(query: str) -> str:
    """Pick the model to answer `query` with."""
    return CHEAP_MODEL if classify_complexity(query) == "simple" else PREMIUM_MODEL


# ---------------------------------------------------------------------------
# 3. Prompt cache
# ---------------------------------------------------------------------------


class PromptCache:
    """Exact-match cache for completed answers."""

    def __init__(self):
        self.store: dict[str, str] = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(model: str, prompt: str) -> str:
        normalised = prompt.strip().lower()
        return hashlib.sha256(f"{model}:{normalised}".encode()).hexdigest()

    def get(self, model: str, prompt: str) -> str | None:
        cached = self.store.get(self.key(model, prompt))
        if cached is None:
            self.misses += 1
            return None
        self.hits += 1
        return cached

    def set(self, model: str, prompt: str, response: str) -> None:
        self.store[self.key(model, prompt)] = response

    @property
    def hit_rate(self) -> float:
        """Fraction of lookups served from cache."""
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


# ---------------------------------------------------------------------------
# Scripted client and the wiring that uses all three — provided.
# ---------------------------------------------------------------------------


def make_scripted_client(answer: str = "Warp core efficiency is holding at 94%."):
    """A stand-in for an OpenAI client, reporting usage in the real shape."""

    def create(*, model: str, input: list[dict], **kwargs):  # noqa: A002
        prompt = " ".join(message["content"] for message in input)
        input_tokens = max(1, len(prompt) // 4)
        output_tokens = max(1, len(answer) // 4)
        return SimpleNamespace(
            output_text=answer,
            usage=SimpleNamespace(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
        )

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def answer_query(client, query: str, tracker: CostTracker, cache: PromptCache) -> dict:
    """Route, cache, and bill one query."""
    model = choose_model(query)

    cached = cache.get(model, query)
    if cached is not None:
        return {"answer": cached, "model": model, "cached": True, "cost_usd": 0.0}

    if not tracker.within_budget():
        return {"answer": None, "model": model, "cached": False, "refused": True}

    response = client.responses.create(
        model=model,
        reasoning={"effort": "none"},
        input=[{"role": "user", "content": query}],
    )
    cost = tracker.record(
        model, response.usage.input_tokens, response.usage.output_tokens
    )
    cache.set(model, query, response.output_text)
    return {
        "answer": response.output_text,
        "model": model,
        "cached": False,
        "cost_usd": cost,
    }


QUERIES = [
    "What is the warp core efficiency?",
    "Who is the chief engineer?",
    "What is the warp core efficiency?",  # repeat — should hit the cache
    "Compare the ion storm damage against the hull stress model and recommend a repair order.",
    "How many crew are in engineering?",
]


if __name__ == "__main__":
    client = make_scripted_client()
    tracker = CostTracker(session_budget=60)  # deliberately tight, to show a refusal
    cache = PromptCache()

    for query in QUERIES:
        result = answer_query(client, query, tracker, cache)
        if result.get("refused"):
            print(f"  refused (budget spent)  {query[:60]}")
            continue
        tag = "cached" if result["cached"] else f"${result['cost_usd']:.5f}"
        print(f"  {result['model']:<11} {tag:<9} {query[:60]}")

    print(f"\n  {tracker.summary()}")
    print(f"  cache hit rate: {cache.hit_rate:.0%}")
