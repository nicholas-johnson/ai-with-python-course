"""
Exercise 04 — Faithfulness (Solution)

Split an answer into claims and check each one against retrieved context.
"""

from __future__ import annotations

import os
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def extract_claims(client: OpenAI, answer: str) -> list[str]:
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[{
            "role": "user",
            "content": (
                "Extract each distinct factual claim from this text. "
                "Write one claim per line. Do not add numbering or bullets.\n\n"
                f"Text: {answer}"
            ),
        }],
        temperature=0,
    )
    text = (response.output_text or "").strip()
    return [line.strip() for line in text.split("\n") if line.strip()]


def check_support(client: OpenAI, claim: str, context: str) -> str:
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[{
            "role": "user",
            "content": (
                "Does this context support the following claim? "
                "Answer exactly 'supported' or 'unsupported'.\n\n"
                f"Claim: {claim}\n\n"
                f"Context: {context}"
            ),
        }],
        temperature=0,
    )
    verdict = (response.output_text or "").strip().lower()
    if "unsupported" in verdict:
        return "unsupported"
    if "supported" in verdict:
        return "supported"
    return "unsupported"


def score_faithfulness(client: OpenAI, answer: str, context: str) -> dict:
    claims = extract_claims(client, answer)
    rows = []
    for claim in claims:
        supported = check_support(client, claim, context) == "supported"
        rows.append({"claim": claim, "supported": supported})
    n = len(rows)
    n_ok = sum(1 for r in rows if r["supported"])
    return {
        "claims": rows,
        "num_claims": n,
        "num_supported": n_ok,
        "faithfulness": (n_ok / n) if n else 1.0,
    }
