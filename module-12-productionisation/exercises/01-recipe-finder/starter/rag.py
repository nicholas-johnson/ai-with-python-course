"""RAG pipeline — indexing, hybrid search, and reranking."""

import json

import chromadb
from openai import OpenAI

from .config import EMBEDDING_MODEL, OPENAI_MODEL

client = OpenAI()


def build_index(recipes: list[dict]) -> tuple[chromadb.Collection, chromadb.ClientAPI]:
    """Embed recipe text into a ChromaDB in-memory collection.

    Steps:
    1. Create an in-memory ChromaDB client
    2. Delete existing "recipes" collection if it exists, then create a new one
    3. For each recipe, combine title + description + ingredients into one text string
    4. Store metadata: recipe_id, title, cuisine, dietary, cook_time
    5. Embed in batches of 100 using client.embeddings.create
    6. Add documents, embeddings, metadatas, and ids to the collection
    7. Return (collection, chroma_client)
    """
    chroma = chromadb.Client()
    try:
        chroma.delete_collection("recipes")
    except Exception:
        pass
    collection = chroma.create_collection("recipes")

    # TODO: build document list, embed in batches, add to collection

    return collection, chroma


def _bm25_search(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Simple keyword search using term matching against documents.

    Steps:
    1. Get all documents and metadatas from the collection
    2. Split query into lowercase terms
    3. Score each document by counting how many query terms appear in it
    4. Sort by score descending, return top k
    """
    # TODO: implement keyword search
    return []


def _vector_search(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Semantic search using vector embeddings.

    Steps:
    1. Embed the query using client.embeddings.create
    2. Call collection.query with the query embedding
    3. Return results as list of dicts with id, document, metadata, distance
    """
    # TODO: implement vector search
    return []


def hybrid_search(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Combine BM25 keyword search and vector search using Reciprocal Rank Fusion.

    Steps:
    1. Run _bm25_search and _vector_search
    2. For each result list, compute RRF score: 1/(rrf_k + rank + 1) where rrf_k=60
    3. Sum RRF scores for documents appearing in both lists
    4. Sort by combined RRF score descending
    5. Return top k results with rrf_score added
    """
    # TODO: implement hybrid search with RRF
    return _vector_search(query, collection, k)


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Use the LLM to rerank search results by relevance.

    Steps:
    1. Format candidates as numbered list with title and truncated text
    2. Ask the LLM to return a JSON array of numbers ordered by relevance
    3. Parse the JSON response and reorder results accordingly
    4. Fall back to original order if parsing fails
    """
    # TODO: implement LLM-based reranking
    return results[:top_k]


def format_results(hits: list[dict]) -> list[dict]:
    """Format search hits for the API response."""
    formatted = []
    for hit in hits:
        meta = hit.get("metadata", {})
        formatted.append({
            "id": meta.get("recipe_id", hit.get("id", "")),
            "title": meta.get("title", ""),
            "cuisine": meta.get("cuisine", ""),
            "dietary": meta.get("dietary", ""),
            "cook_time": meta.get("cook_time", ""),
            "score": round(hit.get("rrf_score", 1.0 - hit.get("distance", 0)), 4),
        })
    return formatted
