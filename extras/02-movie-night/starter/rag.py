"""RAG pipeline — embed movie plots into ChromaDB and search by mood."""

import chromadb
from openai import OpenAI
from .config import OPENAI_MODEL, EMBEDDING_MODEL

client = OpenAI()


def build_index(movies: list[dict]) -> chromadb.Collection:
    """Embed plot summaries into an in-memory ChromaDB collection."""
    chroma = chromadb.Client()

    try:
        chroma.delete_collection("movies")
    except Exception:
        pass

    collection = chroma.create_collection(
        name="movies",
        metadata={"hnsw:space": "cosine"},
    )

    # TODO: Build the vector index
    # 1. For each movie, create a document string: "{title} ({year}). {plot}"
    # 2. Collect ids (as strings), documents, and metadatas (title, year, director, rating, genres)
    # 3. Batch embed documents using _get_embeddings (batch_size=100)
    # 4. Add each batch to the collection with collection.add()

    return collection


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def search_by_mood(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Semantic search for movies matching a mood/description query."""
    # TODO: Implement vector search
    # 1. Embed the query using _get_embeddings
    # 2. Call collection.query() with query_embeddings, n_results=k
    # 3. Build a list of match dicts with: id, title, year, director, rating, genres,
    #    score (1 - distance), and summary (document text)
    # 4. Return the matches list
    pass


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Use the LLM to rerank search results by relevance to the query."""
    if not results:
        return []

    # TODO: Implement LLM-based reranking
    # 1. Format the results as a numbered list: "1. Title (Year) — summary[:120]"
    # 2. Call the LLM asking it to return the top_k most relevant movie numbers
    #    as comma-separated values (e.g. "3,1,5")
    # 3. Parse the response into indices and return the reranked results
    # 4. Fall back to results[:top_k] if parsing fails
    pass
