"""
Exercise 02 — Re-ranking (Solution)

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
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Rate how relevant this passage is to the query on a scale "
                f"of 0 to 10. Respond with ONLY a number.\n\n"
                f"Query: {query}\n\n"
                f"Passage: {passage}"
            ),
        }],
        temperature=0,
    )
    try:
        return float(response.choices[0].message.content.strip())
    except ValueError:
        return 0.0


def rerank(
    client: OpenAI,
    query: str,
    passages: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Re-rank passages by scoring each one against the query.
    """
    scored = []
    for passage in passages:
        score = score_relevance(client, query, passage["text"])
        scored.append({**passage, "rerank_score": score})
    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    return scored[:top_k]


def two_stage_retrieve(
    client: OpenAI,
    query: str,
    retrieve_fn,
    retrieve_k: int = 20,
    final_k: int = 5,
) -> list[dict]:
    """
    Two-stage retrieval: first retrieve broadly, then re-rank for precision.
    """
    candidates = retrieve_fn(query, retrieve_k)
    return rerank(client, query, candidates, top_k=final_k)
