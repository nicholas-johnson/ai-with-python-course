"""
Exercise 02 — Re-ranking

Re-rank retrieved passages using an LLM scorer for higher precision.
"""

from openai import OpenAI


def score_relevance(
    client: OpenAI,
    query: str,
    passage: str,
) -> float:
    """
    Score the relevance of a passage to a query on a scale of 0-10.

    Uses the LLM to evaluate how well the passage answers the query.

    Args:
        client: OpenAI client.
        query: The user's question.
        passage: A candidate passage.

    Returns:
        A float score between 0 and 10.

    TODO:
    - Send a prompt to gpt-4o-mini asking it to rate relevance 0-10
    - The prompt should include both the query and passage
    - Ask for just a number in the response
    - Parse and return the float score
    """
    # TODO: implement LLM relevance scoring
    pass


def rerank(
    client: OpenAI,
    query: str,
    passages: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Re-rank passages by scoring each one against the query.

    Each passage is a dict with at least a "text" key.
    Returns passages sorted by relevance score, with a "rerank_score" key added.

    TODO:
    - Score each passage using score_relevance
    - Add the score as "rerank_score" to each passage dict
    - Sort by rerank_score descending
    - Return top_k passages
    """
    # TODO: implement re-ranking
    pass


def two_stage_retrieve(
    client: OpenAI,
    query: str,
    retrieve_fn,
    retrieve_k: int = 20,
    final_k: int = 5,
) -> list[dict]:
    """
    Two-stage retrieval: first retrieve broadly, then re-rank for precision.

    Args:
        client: OpenAI client.
        query: The user's question.
        retrieve_fn: A function that takes (query, top_k) and returns passages.
        retrieve_k: Number of candidates to retrieve in stage 1.
        final_k: Number of results to return after re-ranking.

    TODO:
    - Call retrieve_fn to get retrieve_k candidates
    - Re-rank them with the rerank function
    - Return final_k results
    """
    # TODO: implement two-stage retrieval
    pass
