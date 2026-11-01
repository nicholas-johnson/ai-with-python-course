"""
Exercise 03 — LLM-as-Judge (Solution)

Evaluate RAG answers using an LLM judge that scores
correctness, completeness, and relevance.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DATA_DIR = Path(__file__).parent / "data"


class JudgeScores(BaseModel):
    correctness: int = Field(ge=1, le=5, description="Are the facts accurate?")
    completeness: int = Field(ge=1, le=5, description="Does it cover all key points from the reference?")
    relevance: int = Field(ge=1, le=5, description="Does it directly address the question?")
    explanation: str


def llm_judge(
    client: OpenAI,
    question: str,
    answer: str,
    reference: str,
) -> dict:
    """Use an LLM to evaluate an answer against a reference."""
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=JudgeScores,
        input=[{
            "role": "user",
            "content": (
                f"Evaluate this answer against the reference answer.\n\n"
                f"Question: {question}\n\n"
                f"Candidate Answer: {answer}\n\n"
                f"Reference Answer: {reference}\n\n"
                f"Score each dimension from 1 (worst) to 5 (best):\n"
                f"- Correctness: Are the facts accurate?\n"
                f"- Completeness: Does it cover all key points from the reference?\n"
                f"- Relevance: Does it directly address the question?"
            ),
        }],
        temperature=0,
    )
    if response.output_parsed is None:
        return {
            "correctness": 1,
            "completeness": 1,
            "relevance": 1,
            "explanation": "Judge refused to score this answer.",
        }
    return response.output_parsed.model_dump()


def evaluate_dataset(
    client: OpenAI,
    test_cases: list[dict],
) -> list[dict]:
    """Run LLM evaluation on a dataset of test cases."""
    results = []
    for case in test_cases:
        scores = llm_judge(
            client,
            question=case["question"],
            answer=case["answer"],
            reference=case["reference"],
        )
        results.append({**case, **scores})
    return results


def compute_summary(results: list[dict]) -> dict:
    """Compute summary statistics from evaluation results."""
    n = len(results)
    if n == 0:
        return {
            "avg_correctness": 0.0,
            "avg_completeness": 0.0,
            "avg_relevance": 0.0,
            "num_cases": 0,
        }
    return {
        "avg_correctness": sum(r["correctness"] for r in results) / n,
        "avg_completeness": sum(r["completeness"] for r in results) / n,
        "avg_relevance": sum(r["relevance"] for r in results) / n,
        "num_cases": n,
    }


def load_cases(config: str) -> list[dict]:
    return json.loads((DATA_DIR / "judge_cases.json").read_text())[config]


def make_canned_judge(config: str, cases: list[dict]):
    """A stand-in for the judge model so this runs with no API key."""
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
        summary = compute_summary(results)

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
