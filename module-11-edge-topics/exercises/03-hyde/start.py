"""
Exercise 03 — HyDE (Hypothetical Document Embeddings)

Generate a hypothetical answer, embed it, and use that embedding
to search for real documents in vector space.
"""

from openai import OpenAI


def generate_hypothetical_document(client: OpenAI, query: str) -> str:
    """
    Generate a hypothetical document that would answer the query.

    The document does not need to be factually correct — it just needs
    to look like a real answer in structure and vocabulary.

    Args:
        client: OpenAI client.
        query: The user's question.

    Returns:
        A paragraph-length hypothetical answer.

    TODO:
    - Prompt gpt-4o-mini to write a paragraph answering the query
    - Tell the model it doesn't need to be factually correct
    - Return the generated text
    """
    # TODO: implement hypothetical document generation
    pass


def embed_text(client: OpenAI, text: str) -> list[float]:
    """
    Get an embedding vector for the given text.

    Args:
        client: OpenAI client.
        text: Text to embed.

    Returns:
        Embedding vector as a list of floats.

    TODO:
    - Use text-embedding-3-small model
    - Return the embedding vector
    """
    # TODO: implement embedding
    pass


def hyde_search(
    client: OpenAI,
    query: str,
    collection,
    n_results: int = 5,
) -> dict:
    """
    Full HyDE pipeline: generate hypothetical doc, embed it, search.

    Args:
        client: OpenAI client.
        query: The user's question.
        collection: A chromadb collection with .query() method.
        n_results: Number of results to return.

    Returns:
        dict with keys:
        - "hypothetical_document": the generated text
        - "results": the search results from the collection

    TODO:
    - Generate a hypothetical document
    - Embed the hypothetical document
    - Query the collection with the embedding
    - Return both the hypothetical doc and the results
    """
    # TODO: implement HyDE search
    pass
