"""
Exercise 03 — LLM-as-Judge

Evaluate RAG answers using an LLM judge that scores
correctness, completeness, and relevance.
"""

from __future__ import annotations

import os

from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def llm_judge(
    client: OpenAI,
    question: str,
    answer: str,
    reference: str,
) -> dict:
    """
    Use an LLM to evaluate an answer against a reference.

    Args:
        client: OpenAI client.
        question: The original question.
        answer: The candidate answer to evaluate.
        reference: The reference (gold) answer.

    Returns:
        Dict with keys:
        - "correctness": int (1-5)
        - "completeness": int (1-5)
        - "relevance": int (1-5)
        - "explanation": str

    TODO:
    - Define a Pydantic model JudgeScores (above this function) with
      correctness/completeness/relevance: int = Field(ge=1, le=5) and explanation: str
    - Prompt the model (MODEL) to evaluate the answer on three dimensions,
      using client.responses.parse(..., text_format=JudgeScores)
    - Return response.output_parsed.model_dump()
    - If response.output_parsed is None (the model refused), return scores of 1
    """
    # TODO: implement LLM judge
    pass


def evaluate_dataset(
    client: OpenAI,
    test_cases: list[dict],
) -> list[dict]:
    """
    Run LLM evaluation on a dataset of test cases.

    Each test case has: "question", "answer", "reference".

    Returns a list of evaluation results (one per test case),
    each with the original test case data plus the judge's scores.

    TODO:
    - For each test case, run llm_judge
    - Combine the test case data with the judge's scores
    - Return the full list of results
    """
    # TODO: implement dataset evaluation
    pass


def compute_summary(results: list[dict]) -> dict:
    """
    Compute summary statistics from evaluation results.

    Args:
        results: List of evaluation result dicts (from evaluate_dataset).

    Returns:
        Dict with average scores:
        - "avg_correctness": float
        - "avg_completeness": float
        - "avg_relevance": float
        - "num_cases": int

    TODO:
    - Calculate the average of each score dimension
    - Return a summary dict
    """
    # TODO: implement summary computation
    pass


if __name__ == "__main__":
    import json
    from unittest.mock import MagicMock

    canned = {
        "correctness": 4,
        "completeness": 2,
        "relevance": 5,
        "explanation": "Correct but only mentions one of three causes.",
    }
    client = MagicMock()

    def fake_parse(*, text_format, **kwargs):
        return MagicMock(output_text=json.dumps(canned), output_parsed=text_format(**canned))

    client.responses.parse.side_effect = fake_parse

    cases = [
        {
            "question": "What causes warp core instability?",
            "answer": "Crystal degradation causes it.",
            "reference": (
                "Dilithium crystal degradation, plasma injection asymmetry, "
                "and magnetic containment fluctuations."
            ),
        },
        {
            "question": "Who leads engineering?",
            "answer": "Lt. Torres leads engineering.",
            "reference": "Chief Engineer Mira Chen leads engineering on Pathfinder.",
        },
    ]
    results = evaluate_dataset(client, cases)
    summary = compute_summary(results)
    print("LLM-as-judge (mocked client, no API key)\n")
    if results is None or summary is None:
        print("  not implemented")
    else:
        for row in results:
            print(
                f"  Q: {row['question']}\n"
                f"     correctness={row['correctness']} completeness={row['completeness']} "
                f"relevance={row['relevance']}"
            )
        print(
            f"\n  avg correctness={summary['avg_correctness']:.2f}  "
            f"completeness={summary['avg_completeness']:.2f}  "
            f"relevance={summary['avg_relevance']:.2f}  n={summary['num_cases']}"
        )
