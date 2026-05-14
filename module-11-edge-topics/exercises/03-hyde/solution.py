"""
Exercise 03 — HyDE (Hypothetical Document Embeddings) (Solution)

Generate a hypothetical answer, embed it, and use that embedding
to search for real documents in vector space.
"""

from openai import OpenAI


def generate_hypothetical_document(client: OpenAI, query: str) -> str:
    """
    Generate a hypothetical document that would answer the query.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Write a short, detailed paragraph that answers this question. "
                f"It does not need to be factually correct — just write what a "
                f"good answer would look like in terms of structure, vocabulary, "
                f"and level of detail.\n\n"
                f"Question: {query}"
            ),
        }],
        temperature=0.7,
    )
    return response.choices[0].message.content


def embed_text(client: OpenAI, text: str) -> list[float]:
    """
    Get an embedding vector for the given text.
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def hyde_search(
    client: OpenAI,
    query: str,
    collection,
    n_results: int = 5,
) -> dict:
    """
    Full HyDE pipeline: generate hypothetical doc, embed it, search.
    """
    hypothetical_doc = generate_hypothetical_document(client, query)
    embedding = embed_text(client, hypothetical_doc)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
    )
    return {
        "hypothetical_document": hypothetical_doc,
        "results": results,
    }
