"""RAG pipeline — index and search destinations with ChromaDB."""

from openai import OpenAI
import chromadb

from .config import EMBEDDING_MODEL

client = OpenAI()


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for a text string."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def build_index(destinations: list[dict]) -> chromadb.Collection:
    """Embed destination and attraction descriptions into a ChromaDB collection.

    TODO:
    - Create a ChromaDB in-memory client
    - Create/get collection named "travel_destinations" with cosine space
    - For each destination:
      - Create a document string: "{name} — {description} Tags: {tags}"
      - Use id format: "dest_{id}"
      - Add metadata: type="destination", dest_id, name, country
    - For each attraction within a destination:
      - Create document: "{attraction_name} in {dest_name} — {attraction_description}"
      - Use id format: "attr_{dest_id}_{index}"
      - Add metadata: type="attraction", dest_id, dest_name, attraction_name, category
    - Batch embed all documents using client.embeddings.create
    - Add all documents, ids, metadatas, and embeddings to the collection
    - Return the collection
    """
    pass


def search_destinations(query: str, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """Search destinations by interest or description.

    TODO:
    - Embed the query using get_embedding
    - Query the collection with where={"type": "destination"}
    - Return list of dicts with: id, document, metadata, distance
    """
    pass


def search_attractions(
    query: str, dest_id: str, collection: chromadb.Collection, k: int = 10
) -> list[dict]:
    """Search attractions within a specific destination.

    TODO:
    - Embed the query
    - Query collection with where={"$and": [{"type": "attraction"}, {"dest_id": dest_id}]}
    - Return list of dicts with: id, document, metadata, distance
    """
    pass
