"""
Exercise 04 — Faithfulness

Split an answer into claims and check each one against retrieved context.
Faithfulness = supported claims / total claims.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


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


if __name__ == "__main__":
    from unittest.mock import MagicMock

    here = Path(__file__).parent / "data" / "grounding_cases.json"
    cases = json.loads(here.read_text())

    # Scripted: first call extracts claims (two lines), then two support verdicts.
    scripts = {
        "grounded-warp": [
            "The warp core is at 94% efficiency.\n"
            "Plasma conduit 7-B has a minor fluctuation.",
            "supported",
            "supported",
        ],
        "hallucinated-temp": [
            "The warp core is at 94% efficiency.\nCore temperature is 9000K.",
            "supported",
            "unsupported",
        ],
        "kepler-extra": [
            "Pathfinder arrived at Kepler-442 and raised shields to level 2.\n"
            "The crew found a derelict Romulan scout.",
            "supported",
            "unsupported",
        ],
    }

    print("Faithfulness (mocked client, no API key)\n")
    for case in cases:
        queue = list(scripts[case["id"]])

        def create(**kwargs):
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = queue.pop(0)
            return resp

        client = MagicMock()
        client.chat.completions.create.side_effect = create
        result = score_faithfulness(client, case["answer"], case["context"])
        if result is None:
            print(f"  {case['id']}: not implemented")
            continue
        print(
            f"  {case['id']:20}  faithfulness={result['faithfulness']:.2f}  "
            f"{result['num_supported']}/{result['num_claims']} supported"
        )
