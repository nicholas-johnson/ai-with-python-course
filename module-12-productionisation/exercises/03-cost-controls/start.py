"""
Exercise 03 — Cost Controls

Three levers that decide what a request costs: a budget that refuses work
once it is spent, a router that sends easy questions to a cheap model, and
a cache that does not pay twice for the same question.

No API key: a scripted client returns canned answers and token counts in
the shape the real Responses API uses.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

CHEAP_MODEL = "gpt-6-luna"
PREMIUM_MODEL = "gpt-6-sol"

# Words that signal a lookup rather than a piece of reasoning.
SIMPLE_MARKERS = ("what", "who", "when", "where", "list", "define", "how many")


# ---------------------------------------------------------------------------
# 1. Budget tracking
# ---------------------------------------------------------------------------


class CostTracker:
    """
    Tracks token usage against a session and a daily budget.

    Budgets are in tokens because that is the number the API hands back on
    every response. The USD figure is derived for reporting.

    Args:
        session_budget: Tokens this conversation may use.
        daily_budget: Tokens the whole deployment may use today.
    """

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
        """
        Add one call's usage and return what it cost in USD.

        Rates are per 1,000 tokens and differ between input and output —
        output is the expensive side, and reasoning tokens are billed as
        output, which is why `reasoning={"effort": "none"}` saves money.

        An unknown model should fall back to the PREMIUM_MODEL rate. Guessing
        high means a new model name shows up as an overestimate rather than
        quietly costing nothing.

        TODO:
        - Look up the rates for `model`, defaulting to the PREMIUM_MODEL entry.
        - cost = input_tokens / 1000 * input_rate + output_tokens / 1000 * output_rate
        - Add the token total to session_tokens and daily_tokens.
        - Add cost to session_cost_usd, increment calls, and return cost.
        """
        # TODO: record usage and return the cost
        pass

    def within_budget(self) -> bool:
        """
        True while both budgets have room left.

        TODO:
        - session_tokens < session_budget AND daily_tokens < daily_budget.
        """
        # TODO: implement the budget check
        pass

    def summary(self) -> str:
        """One-line usage report. Provided."""
        return (
            f"{self.calls} calls | "
            f"{self.session_tokens:,}/{self.session_budget:,} session tokens | "
            f"${self.session_cost_usd:.4f}"
        )


# ---------------------------------------------------------------------------
# 2. Model tiering
# ---------------------------------------------------------------------------


def classify_complexity(query: str) -> str:
    """
    Label a query "simple" or "complex".

    "Simple" means a lookup — a fact the model either knows or can read
    straight out of context. "Complex" means it has to reason, compare, or
    plan. The heuristic here is deliberately crude; a real router would use
    a cheap model to classify, which is itself an argument for the pattern.

    TODO:
    - Lowercase the query.
    - Return "simple" if any SIMPLE_MARKERS appears in it, else "complex".
    """
    # TODO: implement the classifier
    pass


def choose_model(query: str) -> str:
    """
    Pick the model to answer `query` with.

    TODO:
    - CHEAP_MODEL for "simple", PREMIUM_MODEL for anything else.
    """
    # TODO: implement the router
    pass


# ---------------------------------------------------------------------------
# 3. Prompt cache
# ---------------------------------------------------------------------------


class PromptCache:
    """
    Exact-match cache for completed answers.

    The same question asked twice costs twice unless you keep the answer.
    Keys hash the model alongside the prompt, because the same question
    answered by `gpt-6-luna` and `gpt-6-sol` are different results and must
    not collide.
    """

    def __init__(self):
        self.store: dict[str, str] = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(model: str, prompt: str) -> str:
        """
        Build the cache key for one (model, prompt) pair.

        Strip and lowercase the prompt first. "Warp status?" and
        "  warp status? " are the same question, and treating them as two
        entries halves the hit rate for no reason.

        TODO:
        - Normalise: prompt.strip().lower().
        - Hash f"{model}:{normalised}" with hashlib.sha256 and return .hexdigest().
          Encode the string to bytes first.
        """
        # TODO: implement the key
        pass

    def get(self, model: str, prompt: str) -> str | None:
        """
        Look up a cached answer, counting the hit or the miss.

        TODO:
        - Build the key, look it up in self.store.
        - Found: increment hits, return the answer.
        - Not found: increment misses, return None.
        """
        # TODO: implement the lookup
        pass

    def set(self, model: str, prompt: str, response: str) -> None:
        """
        Store an answer under its key.

        TODO:
        - self.store[self.key(model, prompt)] = response
        """
        # TODO: implement the store
        pass

    @property
    def hit_rate(self) -> float:
        """Fraction of lookups served from cache. Provided."""
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


# ---------------------------------------------------------------------------
# Scripted client and the wiring that uses all three — provided.
# ---------------------------------------------------------------------------


def make_scripted_client(answer: str = "Warp core efficiency is holding at 94%."):
    """
    A stand-in for an OpenAI client. Reports token counts in the same shape
    as the real Responses API, scaled off the length of the prompt.
    """

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
    """
    Route, cache, and bill one query. Provided — it wires up all three pieces.

    The order matters: check the cache before the budget, because a cached
    answer costs nothing and there is no reason to refuse it.
    """
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
