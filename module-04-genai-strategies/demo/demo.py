"""
Module 4 Demo — GenAI Strategies
Run:  python module-04-genai-strategies/demo/demo.py

Walks through the module in one script:
  Part 1: Model selection — compare GPT-4o vs GPT-4o-mini on the same task
  Part 2: Guardrails — schema validation, content filtering, confidence gating

Requires: OPENAI_API_KEY environment variable.
"""

import json
import time

from openai import OpenAI
from pydantic import BaseModel, ValidationError

MODEL_PREMIUM = "gpt-4o"
MODEL_BUDGET = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")


# ---------------------------------------------------------------------------
# Part 1: Model selection — quality vs cost vs speed
# ---------------------------------------------------------------------------


def demo_model_selection(client: OpenAI):
    section("Part 1: Model Selection — Quality vs Cost vs Speed")

    task_prompt = (
        "Explain the attention mechanism in transformers in exactly 2 sentences. "
        "Return JSON: {\"explanation\": \"...\", \"confidence\": 0.0-1.0}"
    )
    system = "You are a technical writer. Return ONLY valid JSON."

    results = {}
    for model_name in [MODEL_PREMIUM, MODEL_BUDGET]:
        start = time.time()
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": task_prompt},
            ],
            response_format={"type": "json_object"},
        )
        elapsed = time.time() - start
        usage = resp.usage

        results[model_name] = {
            "response": resp.choices[0].message.content,
            "latency_ms": int(elapsed * 1000),
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
        }

    print(f"  Task: '{task_prompt[:60]}...'\n")

    for model_name, data in results.items():
        label = "Premium" if model_name == MODEL_PREMIUM else "Budget"
        print(f"  {label} ({model_name}):")
        print(f"    Latency:    {data['latency_ms']}ms")
        print(f"    Tokens:     {data['prompt_tokens']} prompt + {data['completion_tokens']} completion")
        print(f"    Response:   {data['response'][:120]}...")
        print()

    print("  Key points:")
    print("  • GPT-4o-mini is faster and cheaper — often good enough for structured tasks")
    print("  • GPT-4o produces higher-quality reasoning when needed")
    print("  • Start with the cheapest model that passes your eval suite")
    print("  • Route: simple tasks -> mini, complex reasoning -> premium")


# ---------------------------------------------------------------------------
# Part 2: Guardrails — schema + filter + confidence
# ---------------------------------------------------------------------------


class ResearchOutput(BaseModel):
    title: str
    summary: str
    confidence: float


def demo_guardrails(client: OpenAI):
    section("Part 2: Guardrails — Defence in Depth")

    BLOCKED_TERMS = ["classified", "top secret", "restricted"]

    def run_guardrails(raw_response: str) -> dict:
        """Chain: schema validation -> content filter -> confidence gate."""
        # Step 1: Schema
        try:
            data = ResearchOutput.model_validate_json(raw_response)
        except ValidationError as e:
            return {"passed": False, "reason": f"Schema validation failed: {e.error_count()} errors"}

        # Step 2: Content filter
        text = raw_response.lower()
        for term in BLOCKED_TERMS:
            if term in text:
                return {"passed": False, "reason": f"Blocked term: '{term}'"}

        # Step 3: Confidence gate
        if data.confidence < 0.7:
            return {"passed": False, "reason": f"Low confidence: {data.confidence}"}

        return {"passed": True, "data": data.model_dump()}

    print("  Testing 3 cases through the guardrail chain:\n")

    # Case 1: Valid response
    print("  Case 1: Valid response")
    valid = '{"title": "Attention Is All You Need", "summary": "Introduced the transformer architecture.", "confidence": 0.95}'
    result = run_guardrails(valid)
    status = "PASS" if result["passed"] else f"FAIL ({result['reason']})"
    print(f"    Input:  {valid[:80]}...")
    print(f"    Result: {status}\n")

    # Case 2: Malformed JSON
    print("  Case 2: Malformed JSON (missing required field)")
    malformed = '{"title": "Something", "confidence": 0.9}'
    result = run_guardrails(malformed)
    status = "PASS" if result["passed"] else f"FAIL ({result['reason']})"
    print(f"    Input:  {malformed}")
    print(f"    Result: {status}\n")

    # Case 3: Blocked content
    print("  Case 3: Blocked content")
    blocked = '{"title": "Classified Report", "summary": "This is classified material.", "confidence": 0.99}'
    result = run_guardrails(blocked)
    status = "PASS" if result["passed"] else f"FAIL ({result['reason']})"
    print(f"    Input:  {blocked[:80]}...")
    print(f"    Result: {status}\n")

    # Case 4: Low confidence
    print("  Case 4: Low confidence")
    low_conf = '{"title": "Maybe", "summary": "Not sure about this.", "confidence": 0.3}'
    result = run_guardrails(low_conf)
    status = "PASS" if result["passed"] else f"FAIL ({result['reason']})"
    print(f"    Input:  {low_conf}")
    print(f"    Result: {status}\n")

    print("  Now with a live LLM response:\n")

    resp = client.chat.completions.create(
        model=MODEL_BUDGET,
        messages=[
            {
                "role": "system",
                "content": (
                    "Return JSON: {\"title\": string, \"summary\": string, \"confidence\": float 0-1}. "
                    "Only valid JSON, no markdown."
                ),
            },
            {"role": "user", "content": "Summarise the concept of retrieval-augmented generation."},
        ],
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    print(f"    LLM output: {raw[:100]}...")
    result = run_guardrails(raw)
    status = "PASS" if result["passed"] else f"FAIL ({result['reason']})"
    print(f"    Guardrail:  {status}\n")

    print("  Key points:")
    print("  • Chain guardrails: schema -> filter -> confidence. Fail fast.")
    print("  • Pydantic validates structure and types in one call")
    print("  • Content filters catch things the schema can't")
    print("  • Confidence gating lets the agent say 'I'm not sure' instead of guessing")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    client = OpenAI()

    demo_model_selection(client)
    pause()

    demo_guardrails(client)

    print("\n" + "=" * 60)
    print("  Demo complete. Ready for exercises!")
    print("=" * 60)
