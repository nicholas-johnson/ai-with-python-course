"""
RAG utilities -- provided from Exercise 2 solution.
Import this to get build_grounded_prompt and rag_chat.
"""

from openai import OpenAI
from index_builder import search

client = OpenAI()


def build_grounded_prompt(query: str, passages: list[dict]) -> list[dict]:
    """Construct a grounded prompt with [Source N] labels."""
    context_parts = []
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        context_parts.append(f"[Source {i}: {source}] {p['text']}")

    system = (
        "Answer the question using ONLY the sources below. "
        "Cite sources using [Source N]. "
        "If the sources don't contain the answer, say so."
    )
    context = "\n\n".join(context_parts)
    user_msg = f"{context}\n\nQuestion: {query}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]


def rag_chat(query: str, collection, k: int = 5) -> tuple[str, list[dict]]:
    """Retrieve relevant chunks, build a grounded prompt, and generate an answer."""
    passages = search(collection, query, k)
    messages = build_grounded_prompt(query, passages)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    answer = response.choices[0].message.content
    return answer, passages
