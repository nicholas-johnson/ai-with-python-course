"""
Module 4 Demo — tiktoken: Token Counting & Cost Estimation
Run:  python module-04-genai-strategies/demo/demo_tiktoken.py

Shows how OpenAI tokenizers work: encode/decode, count chat messages,
trim history to a budget, and estimate cost across models.

No API key required — tiktoken runs entirely locally.
"""

from __future__ import annotations

import copy

import tiktoken

# Per-million-token prices (USD). Update from:
# https://openai.com/api/pricing/
DEFAULT_MODEL = "gpt-4o"

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4": {"input": 30.00, "output": 60.00},
}

MODEL_CHOICES = ", ".join(MODEL_PRICING)

SAMPLE_TEXT = (
    "The research assistant fetches web pages, saves notes, and answers "
    "questions about deep-space operations."
)

SAMPLE_MESSAGES = [
    {
        "role": "system",
        "content": "You are a helpful research assistant for deep-space operations.",
    },
    {
        "role": "user",
        "content": "Summarise the latest findings on orbital debris mitigation.",
    },
    {
        "role": "assistant",
        "content": "Key strategies include active debris removal, collision avoidance "
        "manoeuvres, and end-of-life deorbit plans.",
    },
    {
        "role": "user",
        "content": "Save that as a note and fetch the ESA guidelines page.",
    },
]


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def resolve_model(raw: str, default: str = DEFAULT_MODEL) -> str:
    """Return a model name tiktoken recognises; fall back on invalid input."""
    model = raw.strip() or default
    try:
        tiktoken.encoding_for_model(model)
    except KeyError:
        print(
            f"  Unknown model {model!r} — using {default}. "
            f"Valid examples: {MODEL_CHOICES}"
        )
        return default
    return model


def prompt_model() -> str:
    return resolve_model(
        input(f"  OpenAI model name [{DEFAULT_MODEL}] (Enter = default): ")
    )


def count_tokens(text: str, model: str = DEFAULT_MODEL) -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def num_tokens_from_messages(messages: list[dict], model: str = DEFAULT_MODEL) -> int:
    """Count tokens in a chat messages list (OpenAI cookbook formula)."""
    model = resolve_model(model)
    encoding = tiktoken.encoding_for_model(model)

    if "gpt-3.5-turbo" in model:
        tokens_per_message = 4
        tokens_per_name = -1
    else:
        # gpt-4, gpt-4o, gpt-4o-mini, and other modern chat models
        tokens_per_message = 3
        tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value is None:
                continue
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with assistant
    return num_tokens


def enforce_budget(messages: list[dict], max_tokens: int, model: str = DEFAULT_MODEL) -> list[dict]:
    """Drop oldest non-system turns until under budget."""
    trimmed = copy.deepcopy(messages)
    total = num_tokens_from_messages(trimmed, model)
    while total > max_tokens and len(trimmed) > 2:
        removed = trimmed.pop(1)  # keep system prompt at index 0
        total = num_tokens_from_messages(trimmed, model)
        role = removed.get("role", "?")
        preview = str(removed.get("content", ""))[:50]
        print(f"  Dropped {role} turn: {preview!r}…  ({total} tokens remaining)")
    return trimmed


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> tuple[float, float, float]:
    """Return (input_cost, output_cost, total_cost) in USD."""
    prices = MODEL_PRICING[model]
    input_cost = input_tokens * prices["input"] / 1_000_000
    output_cost = output_tokens * prices["output"] / 1_000_000
    return input_cost, output_cost, input_cost + output_cost


def demo_encoding() -> None:
    section("Part 1: Encoding & Decoding")

    text = input(f"  Enter text to tokenize [{SAMPLE_TEXT[:40]}…]: ").strip() or SAMPLE_TEXT
    model = prompt_model()

    enc = tiktoken.encoding_for_model(model)
    token_ids = enc.encode(text)

    print(f"\n  Model:     {model}")
    print(f"  Encoding:  {enc.name}")
    print(f"  Characters: {len(text)}")
    print(f"  Tokens:     {len(token_ids)}")
    print(f"  Token IDs:  {token_ids[:20]}{'…' if len(token_ids) > 20 else ''}")

    print("\n  Individual tokens:")
    for tid in token_ids[:15]:
        piece = enc.decode_single_token_bytes(tid).decode("utf-8", errors="replace")
        print(f"    {tid:6d}  →  {piece!r}")
    if len(token_ids) > 15:
        print(f"    … ({len(token_ids) - 15} more)")

    decoded = enc.decode(token_ids)
    print(f"\n  Round-trip decode matches: {decoded == text}")


def demo_counting() -> None:
    section("Part 2: Token Counting for Chat Messages")

    model = prompt_model()

    print("  Sample conversation (fixed — not your input):\n")
    for msg in SAMPLE_MESSAGES:
        content = str(msg["content"])
        preview = content if len(content) <= 60 else content[:57] + "…"
        print(f"    [{msg['role']:10}] {preview}")

    total = num_tokens_from_messages(SAMPLE_MESSAGES, model)
    print(f"\n  Total tokens (with message overhead): {total}")
    print(f"  Encoding: {tiktoken.encoding_for_model(model).name}")

    print("\n  Per-message breakdown:")
    enc = tiktoken.encoding_for_model(model)
    for msg in SAMPLE_MESSAGES:
        content_tokens = len(enc.encode(str(msg["content"])))
        print(f"    {msg['role']:10}  content={content_tokens:4d}  (+3 overhead in full count)")


def demo_budget() -> None:
    section("Part 3: Budget Enforcement")

    model = prompt_model()
    budget_str = input("  Max tokens [80]: ").strip()
    max_tokens = int(budget_str) if budget_str.isdigit() else 80

    before = num_tokens_from_messages(SAMPLE_MESSAGES, model)
    print(f"\n  Before: {len(SAMPLE_MESSAGES)} messages, {before} tokens")
    print("  Trimming oldest turns (system prompt preserved)…\n")

    after_messages = enforce_budget(SAMPLE_MESSAGES, max_tokens, model)
    after = num_tokens_from_messages(after_messages, model)

    print(f"\n  After:  {len(after_messages)} messages, {after} tokens (budget {max_tokens})")
    print("\n  Remaining conversation:")
    for msg in after_messages:
        preview = str(msg["content"])[:55]
        print(f"    [{msg['role']}] {preview}…")


def demo_costs() -> None:
    section("Part 4: Cost Estimation Across Models")

    text = input(f"  Enter prompt text [sample]: ").strip() or SAMPLE_TEXT
    output_str = input("  Assumed output tokens [150]: ").strip()
    output_tokens = int(output_str) if output_str.isdigit() else 150

    print(f"\n  Prompt ({len(text)} chars):\n    {text!r}\n")
    print(f"  Assumed completion length: {output_tokens} tokens\n")
    print(f"  {'Model':<16} {'Encoding':<14} {'Input':>7} {'Output':>7} "
          f"{'In $':>10} {'Out $':>10} {'Total $':>10}")
    print(f"  {'-'*16} {'-'*14} {'-'*7} {'-'*7} {'-'*10} {'-'*10} {'-'*10}")

    for model in MODEL_PRICING:
        enc = tiktoken.encoding_for_model(model)
        input_tokens = len(enc.encode(text))
        in_cost, out_cost, total = estimate_cost(input_tokens, output_tokens, model)
        print(
            f"  {model:<16} {enc.name:<14} {input_tokens:7d} {output_tokens:7d} "
            f"{in_cost:10.6f} {out_cost:10.6f} {total:10.6f}"
        )



DEMOS = [
    ("Encoding & Decoding", demo_encoding),
    ("Token Counting for Messages", demo_counting),
    ("Budget Enforcement", demo_budget),
    ("Cost Estimation Across Models", demo_costs),
]


def show_menu() -> None:
    print(f"\n{'='*60}")
    print("  Module 4 Demo — tiktoken")
    print(f"{'='*60}\n")
    for i, (title, _) in enumerate(DEMOS, 1):
        print(f"  [{i}] {title}")
    print("\n  [q] Quit")
    print()


def main() -> None:
    while True:
        show_menu()
        choice = input("  Choose a demo: ").strip().lower()

        if choice == "q":
            break
        if choice.isdigit() and 1 <= int(choice) <= len(DEMOS):
            _, func = DEMOS[int(choice) - 1]
            func()
            input("\n  [press Enter to return to menu]\n")
        else:
            print("  Invalid choice, try again.")

    print(f"\n{'='*60}")
    print("  Done. Use token budgets in your research assistant!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
