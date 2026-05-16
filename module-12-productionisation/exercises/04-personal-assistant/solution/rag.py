"""RAG pipeline — embed and search personal notes."""

import chromadb
from openai import OpenAI

from .config import EMBEDDING_MODEL

client = OpenAI()


def build_notes_index(notes: list[dict]) -> chromadb.Collection:
    """Embed notes into a ChromaDB in-memory collection."""
    chroma = chromadb.Client()
    try:
        chroma.delete_collection("notes")
    except Exception:
        pass
    collection = chroma.create_collection("notes")

    documents, metadatas, ids = [], [], []
    for note in notes:
        text = f"{note['title']}. {note['content']}"
        documents.append(text)
        metadatas.append({
            "note_id": note["id"],
            "title": note["title"],
            "tags": ", ".join(note.get("tags", [])),
        })
        ids.append(note["id"])

    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]

        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch_docs)
        embeddings = [item.embedding for item in response.data]

        collection.add(
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_meta,
            ids=batch_ids,
        )

    return collection


def search_notes(query: str, collection: chromadb.Collection, k: int = 5) -> list[dict]:
    """Vector search over the notes collection."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    query_embedding = response.data[0].embedding

    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i].get("title", ""),
            "content": results["documents"][0][i],
            "tags": results["metadatas"][0][i].get("tags", ""),
            "distance": results["distances"][0][i],
        })
    return hits
