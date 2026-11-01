"""Tests for Exercise 03 — Cost Controls."""

import pytest
from start import (
    CHEAP_MODEL,
    PREMIUM_MODEL,
    CostTracker,
    PromptCache,
    answer_query,
    choose_model,
    classify_complexity,
    make_scripted_client,
)


class TestCostTrackerRecord:
    def test_returns_the_cost_in_usd(self):
        tracker = CostTracker()
        # gpt-6-luna: 1000 input @ 0.0001 + 1000 output @ 0.0005
        cost = tracker.record("gpt-6-luna", 1000, 1000)
        assert cost == pytest.approx(0.0006)

    def test_input_and_output_are_priced_differently(self):
        tracker = CostTracker()
        input_heavy = tracker.record("gpt-6-sol", 1000, 0)
        output_heavy = tracker.record("gpt-6-sol", 0, 1000)
        assert input_heavy == pytest.approx(0.002)
        assert output_heavy == pytest.approx(0.01)
        assert output_heavy > input_heavy

    def test_accumulates_tokens_across_calls(self):
        tracker = CostTracker()
        tracker.record("gpt-6-luna", 100, 50)
        tracker.record("gpt-6-luna", 200, 100)
        assert tracker.session_tokens == 450
        assert tracker.daily_tokens == 450

    def test_accumulates_cost_and_call_count(self):
        tracker = CostTracker()
        first = tracker.record("gpt-6-sol", 1000, 1000)
        second = tracker.record("gpt-6-sol", 1000, 1000)
        assert tracker.calls == 2
        assert tracker.session_cost_usd == pytest.approx(first + second)

    def test_unknown_model_falls_back_to_the_premium_rate(self):
        tracker = CostTracker()
        unknown = tracker.record("gpt-7-nova", 1000, 1000)
        premium = CostTracker().record(PREMIUM_MODEL, 1000, 1000)
        assert unknown == pytest.approx(premium)

    def test_cheap_model_costs_less_than_premium(self):
        cheap = CostTracker().record(CHEAP_MODEL, 1000, 1000)
        premium = CostTracker().record(PREMIUM_MODEL, 1000, 1000)
        assert cheap < premium


class TestCostTrackerWithinBudget:
    def test_true_when_fresh(self):
        assert CostTracker(session_budget=1000).within_budget() is True

    def test_true_below_the_session_budget(self):
        tracker = CostTracker(session_budget=1000)
        tracker.record("gpt-6-luna", 400, 400)
        assert tracker.within_budget() is True

    def test_false_at_the_session_budget(self):
        tracker = CostTracker(session_budget=1000)
        tracker.record("gpt-6-luna", 500, 500)  # exactly 1000
        assert tracker.within_budget() is False

    def test_false_over_the_session_budget(self):
        tracker = CostTracker(session_budget=1000)
        tracker.record("gpt-6-luna", 900, 900)
        assert tracker.within_budget() is False

    def test_daily_budget_also_stops_it(self):
        tracker = CostTracker(session_budget=10_000, daily_budget=500)
        tracker.record("gpt-6-luna", 300, 300)
        assert tracker.session_tokens < tracker.session_budget
        assert tracker.within_budget() is False


class TestClassifyComplexity:
    @pytest.mark.parametrize(
        "query",
        [
            "What is the warp core efficiency?",
            "Who is the chief engineer?",
            "How many crew are in engineering?",
            "List the ship systems.",
            "Define ion storm.",
            "When did the storm hit?",
        ],
    )
    def test_lookups_are_simple(self, query):
        assert classify_complexity(query) == "simple"

    @pytest.mark.parametrize(
        "query",
        [
            "Compare the ion storm damage against the hull stress model.",
            "Recommend a repair order for the damaged subsystems.",
            "Explain the trade-off between shield power and warp efficiency.",
        ],
    )
    def test_reasoning_is_complex(self, query):
        assert classify_complexity(query) == "complex"

    def test_is_case_insensitive(self):
        assert classify_complexity("WHO IS THE CAPTAIN?") == "simple"


class TestChooseModel:
    def test_simple_queries_get_the_cheap_model(self):
        assert choose_model("What is the warp core efficiency?") == CHEAP_MODEL

    def test_complex_queries_get_the_premium_model(self):
        assert choose_model("Recommend a repair order.") == PREMIUM_MODEL


class TestPromptCacheKey:
    def test_same_input_gives_the_same_key(self):
        assert PromptCache.key("gpt-6-luna", "warp status?") == PromptCache.key(
            "gpt-6-luna", "warp status?"
        )

    def test_different_models_do_not_collide(self):
        assert PromptCache.key("gpt-6-luna", "warp status?") != PromptCache.key(
            "gpt-6-sol", "warp status?"
        )

    def test_different_prompts_do_not_collide(self):
        assert PromptCache.key("gpt-6-luna", "warp status?") != PromptCache.key(
            "gpt-6-luna", "shield status?"
        )

    def test_normalises_whitespace_and_case(self):
        assert PromptCache.key("gpt-6-luna", "  Warp Status? ") == PromptCache.key(
            "gpt-6-luna", "warp status?"
        )


class TestPromptCacheGetSet:
    def test_miss_on_an_empty_cache(self):
        cache = PromptCache()
        assert cache.get("gpt-6-luna", "warp status?") is None
        assert cache.misses == 1
        assert cache.hits == 0

    def test_hit_after_set(self):
        cache = PromptCache()
        cache.set("gpt-6-luna", "warp status?", "Holding at 94%.")
        assert cache.get("gpt-6-luna", "warp status?") == "Holding at 94%."
        assert cache.hits == 1
        assert cache.misses == 0

    def test_hit_survives_whitespace_and_case_differences(self):
        cache = PromptCache()
        cache.set("gpt-6-luna", "warp status?", "Holding at 94%.")
        assert cache.get("gpt-6-luna", "  Warp Status? ") == "Holding at 94%."

    def test_a_different_model_misses(self):
        cache = PromptCache()
        cache.set("gpt-6-luna", "warp status?", "Holding at 94%.")
        assert cache.get("gpt-6-sol", "warp status?") is None

    def test_set_overwrites(self):
        cache = PromptCache()
        cache.set("gpt-6-luna", "warp status?", "old")
        cache.set("gpt-6-luna", "warp status?", "new")
        assert cache.get("gpt-6-luna", "warp status?") == "new"

    def test_hit_rate(self):
        cache = PromptCache()
        cache.set("gpt-6-luna", "warp status?", "Holding at 94%.")
        cache.get("gpt-6-luna", "warp status?")  # hit
        cache.get("gpt-6-luna", "shield status?")  # miss
        assert cache.hit_rate == pytest.approx(0.5)

    def test_hit_rate_of_an_unused_cache_is_zero(self):
        assert PromptCache().hit_rate == 0.0


class TestAnswerQuery:
    def test_routes_a_lookup_to_the_cheap_model_and_bills_it(self):
        client = make_scripted_client("Holding at 94%.")
        tracker, cache = CostTracker(), PromptCache()

        result = answer_query(client, "What is the warp core efficiency?", tracker, cache)
        assert result["model"] == CHEAP_MODEL
        assert result["cached"] is False
        assert result["cost_usd"] > 0
        assert tracker.calls == 1

    def test_second_identical_query_is_free(self):
        client = make_scripted_client("Holding at 94%.")
        tracker, cache = CostTracker(), PromptCache()
        query = "What is the warp core efficiency?"

        answer_query(client, query, tracker, cache)
        tokens_after_first = tracker.session_tokens
        second = answer_query(client, query, tracker, cache)

        assert second["cached"] is True
        assert second["cost_usd"] == 0.0
        assert tracker.calls == 1  # no second API call
        assert tracker.session_tokens == tokens_after_first

    def test_refuses_once_the_budget_is_spent(self):
        client = make_scripted_client("Holding at 94%.")
        tracker, cache = CostTracker(session_budget=1), PromptCache()

        first = answer_query(client, "What is the warp core efficiency?", tracker, cache)
        assert first["cached"] is False

        second = answer_query(client, "Who is the chief engineer?", tracker, cache)
        assert second.get("refused") is True
        assert second["answer"] is None

    def test_cached_answers_are_served_even_over_budget(self):
        client = make_scripted_client("Holding at 94%.")
        tracker, cache = CostTracker(session_budget=1), PromptCache()
        query = "What is the warp core efficiency?"

        answer_query(client, query, tracker, cache)
        assert tracker.within_budget() is False

        repeat = answer_query(client, query, tracker, cache)
        assert repeat["cached"] is True
        assert repeat["answer"] == "Holding at 94%."
