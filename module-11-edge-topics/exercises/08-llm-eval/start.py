"""
Exercise 08 — LLM Eval (LLM-as-Judge)

Evaluate RAG answers using an LLM judge that scores
correctness, completeness, and relevance.
"""

from openai import OpenAI


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
    - Prompt gpt-4o-mini to evaluate the answer on three dimensions
    - Ask for JSON output with the four keys above
    - Parse and return the result
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
