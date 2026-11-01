"""
Exercise 03 — LLM-as-Judge

Evaluate RAG answers using an LLM judge that scores
correctness, completeness, and relevance.

The dataset is the same five ship-log questions used in exercise 02, answered
by both pipeline configs. The averages you produce here feed the scorecard in
exercise 05.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DATA_DIR = Path(__file__).parent / "data"


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


def load_cases(config: str) -> list[dict]:
    """The question/answer/reference triples for one pipeline config. Provided."""
    return json.loads((DATA_DIR / "judge_cases.json").read_text())[config]


def make_canned_judge(config: str, cases: list[dict]):
    """
    A stand-in for the judge model so this runs with no API key. Provided.

    Replays one recorded score per case, in order.
    """
    from unittest.mock import MagicMock

    scores = json.loads((DATA_DIR / "canned_scores.json").read_text())[config]
    queue = [scores[case["id"]] for case in cases]

    def parse(*, text_format, **kwargs):
        canned = queue.pop(0)
        return MagicMock(
            output_text=json.dumps(canned),
            output_parsed=text_format(**canned),
        )

    client = MagicMock()
    client.responses.parse.side_effect = parse
    return client


if __name__ == "__main__":
    print("LLM-as-judge — two configs, one question set, no API key\n")

    for config in ("rag", "rag_rerank"):
        cases = load_cases(config)
        results = evaluate_dataset(make_canned_judge(config, cases), cases)
        summary = compute_summary(results) if results else None
        if summary is None:
            print(f"  {config}: not implemented\n")
            continue

        print(f"  {config}")
        for row in results:
            print(
                f"    {row['id']:18} correctness={row['correctness']} "
                f"completeness={row['completeness']} relevance={row['relevance']}"
            )
            print(f"                       {row['explanation']}")
        print(
            f"    average            correctness={summary['avg_correctness']:.2f}  "
            f"completeness={summary['avg_completeness']:.2f}  "
            f"relevance={summary['avg_relevance']:.2f}  n={summary['num_cases']}\n"
        )
