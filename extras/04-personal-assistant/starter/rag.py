"""RAG pipeline — embed and search personal notes.

Techniques used:
- Vector embeddings with OpenAI's embedding model
- ChromaDB for in-memory vector storage
- Semantic search with cosine similarity
"""

import chromadb
from openai import OpenAI

from .config import EMBEDDING_MODEL

client = OpenAI()


def build_notes_index(notes: list[dict]) -> chromadb.Collection:
    """Embed notes into a ChromaDB in-memory collection.

    Steps:
    1. Create an in-memory ChromaDB client and collection called "notes"
    2. For each note, combine title and content into a single string
    3. Store metadata: note_id, title, tags (comma-separated)
    4. Batch-embed using OpenAI's embedding API
    5. Add documents, embeddings, metadata, and IDs to the collection
    """
    # TODO: Create ChromaDB client and collection
    chroma = chromadb.Client()

    # TODO: Build document strings, metadata, and ID lists from notes

    # TODO: Batch-embed documents using client.embeddings.create()

    # TODO: Add to collection and return it
    pass


def search_notes(query: str, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """Vector search over the notes collection.

    Steps:
    1. Embed the query using the same embedding model
    2. Query the ChromaDB collection with the embedding
    3. Format results as a list of dicts with id, title, content, tags, distance
    """
    # TODO: Embed the query

    # TODO: Query the collection

    # TODO: Format and return results
    pass
