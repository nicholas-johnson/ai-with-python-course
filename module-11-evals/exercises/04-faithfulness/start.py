"""
Exercise 04 — Faithfulness

Split an answer into claims and check each one against retrieved context.
Faithfulness = supported claims / total claims.

The dataset is the same five ship-log questions used in exercises 02 and 03,
answered by both pipeline configs. The averages you produce here feed the
scorecard in exercise 05.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DATA_DIR = Path(__file__).parent / "data"


def extract_claims(client: OpenAI, answer: str) -> list[str]:
    """
    Extract individual factual claims from an answer.

    Args:
        client: OpenAI client.
        answer: Generated answer text.

    Returns:
        A list of claim strings (empty lines stripped).

    TODO:
    - Prompt the model (MODEL) to list each factual claim on its own line
    - Split on newlines and drop blanks
    """
    # TODO: implement claim extraction
    pass


def check_support(client: OpenAI, claim: str, context: str) -> str:
    """
    Check whether `context` supports `claim`.

    Returns exactly "supported" or "unsupported".

    TODO:
    - Prompt the model (MODEL) to answer with those two words only
    - Normalise the verdict (lowercase; treat anything else as unsupported)
    """
    # TODO: implement support check
    pass


def score_faithfulness(client: OpenAI, answer: str, context: str) -> dict:
    """
    Score how grounded an answer is in `context`.

    Returns:
        {
            "claims": [{"claim": str, "supported": bool}, ...],
            "num_claims": int,
            "num_supported": int,
            "faithfulness": float,  # num_supported / num_claims; 1.0 if no claims
        }

    TODO:
    - extract_claims, then check_support for each claim against the full context
    - faithfulness is the ratio; use 1.0 when there are zero claims
    """
    # TODO: implement faithfulness scoring
    pass


def load_cases(config: str) -> list[dict]:
    """Answers and the context each config retrieved for them. Provided."""
    return json.loads((DATA_DIR / "grounding_cases.json").read_text())[config]


def make_scripted_client(script: list[str]):
    """
    A stand-in for the model so this runs with no API key. Provided.

    Replays one claim-extraction reply followed by one verdict per claim.
    """
    from unittest.mock import MagicMock

    queue = list(script)

    def create(**kwargs):
        response = MagicMock()
        response.output_text = queue.pop(0)
        return response

    client = MagicMock()
    client.responses.create.side_effect = create
    return client


if __name__ == "__main__":
    print("Faithfulness — two configs, one question set, no API key\n")

    for config in ("rag", "rag_rerank"):
        cases = load_cases(config)
        scored = []
        for case in cases:
            client = make_scripted_client(case["script"])
            result = score_faithfulness(client, case["answer"], case["context"])
            if result is None:
                break
            scored.append((case, result))

        if len(scored) != len(cases):
            print(f"  {config}: not implemented\n")
            continue

        print(f"  {config}")
        for case, result in scored:
            print(
                f"    {case['id']:18} faithfulness={result['faithfulness']:.2f}  "
                f"{result['num_supported']}/{result['num_claims']} supported"
            )
            for claim in result["claims"]:
                mark = "ok" if claim["supported"] else "!!"
                print(f"                       [{mark}] {claim['claim']}")
        average = sum(r["faithfulness"] for _, r in scored) / len(scored)
        print(f"    average            faithfulness={average:.2f}  n={len(scored)}\n")
