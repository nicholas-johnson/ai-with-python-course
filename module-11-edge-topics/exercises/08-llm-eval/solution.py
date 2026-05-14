"""
Exercise 08 — LLM Eval (LLM-as-Judge) (Solution)

Evaluate RAG answers using an LLM judge that scores
correctness, completeness, and relevance.
"""

import json
from openai import OpenAI


def llm_judge(
    client: OpenAI,
    question: str,
    answer: str,
    reference: str,
) -> dict:
    """
    Use an LLM to evaluate an answer against a reference.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Evaluate this answer against the reference answer.\n\n"
                f"Question: {question}\n\n"
                f"Candidate Answer: {answer}\n\n"
                f"Reference Answer: {reference}\n\n"
                f"Score each dimension from 1 (worst) to 5 (best):\n"
                f"- Correctness: Are the facts accurate?\n"
                f"- Completeness: Does it cover all key points from the reference?\n"
                f"- Relevance: Does it directly address the question?\n\n"
                f'Respond with JSON only: {{"correctness": N, "completeness": N, '
                f'"relevance": N, "explanation": "..."}}'
            ),
        }],
        temperature=0,
    )
    text = response.choices[0].message.content.strip()
    text = text.strip("```json").strip("```").strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "correctness": 1,
            "completeness": 1,
            "relevance": 1,
            "explanation": f"Failed to parse judge response: {text}",
        }
    return result


def evaluate_dataset(
    client: OpenAI,
    test_cases: list[dict],
) -> list[dict]:
    """
    Run LLM evaluation on a dataset of test cases.
    """
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
    """
    Compute summary statistics from evaluation results.
    """
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
