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
    """Embed destination and attraction descriptions into a ChromaDB collection."""
    chroma = chromadb.Client()
    collection = chroma.get_or_create_collection(
        name="travel_destinations",
        metadata={"hnsw:space": "cosine"},
    )

    docs, ids, metadatas = [], [], []

    for dest in destinations:
        dest_text = f"{dest['name']} — {dest['description']} Tags: {', '.join(dest.get('tags', []))}"
        docs.append(dest_text)
        ids.append(f"dest_{dest['id']}")
        metadatas.append({
            "type": "destination",
            "dest_id": dest["id"],
            "name": dest["name"],
            "country": dest.get("country", ""),
        })

        for i, attraction in enumerate(dest.get("attractions", [])):
            attr_text = f"{attraction['name']} in {dest['name']} — {attraction['description']}"
            docs.append(attr_text)
            ids.append(f"attr_{dest['id']}_{i}")
            metadatas.append({
                "type": "attraction",
                "dest_id": dest["id"],
                "dest_name": dest["name"],
                "attraction_name": attraction["name"],
                "category": attraction.get("category", ""),
            })

    embeddings = []
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings.extend([d.embedding for d in response.data])

    collection.add(documents=docs, ids=ids, metadatas=metadatas, embeddings=embeddings)
    return collection


def search_destinations(query: str, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """Search destinations by interest or description."""
    embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        where={"type": "destination"},
    )

    matches = []
    for i, doc in enumerate(results["documents"][0]):
        matches.append({
            "id": results["ids"][0][i],
            "document": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return matches


def search_attractions(
    query: str, dest_id: str, collection: chromadb.Collection, k: int = 10
) -> list[dict]:
    """Search attractions within a specific destination."""
    embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        where={"$and": [{"type": "attraction"}, {"dest_id": dest_id}]},
    )

    matches = []
    for i, doc in enumerate(results["documents"][0]):
        matches.append({
            "id": results["ids"][0][i],
            "document": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return matches
