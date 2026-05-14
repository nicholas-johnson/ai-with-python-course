"""
Index builder -- provided from Exercise 1 solution.
Import this to get load_logs, build_index, search, and chunk_text.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import chromadb
from openai import OpenAI

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ship_logs.json"
client = OpenAI()


@dataclass
class TextChunk:
    text: str
    source_id: str
    chunk_index: int
    metadata: dict


def load_logs() -> list[dict]:
    """Load ship logs from the data directory."""
    return json.loads(DATA_PATH.read_text())


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping windows of chunk_size characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def build_index(
    log_entries: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
    collection_name: str = "ship_logs",
) -> chromadb.Collection:
    """Chunk all logs, embed with OpenAI, and store in ChromaDB."""
    chroma = chromadb.Client()

    try:
        chroma.delete_collection(collection_name)
    except Exception:
        pass
    collection = chroma.create_collection(collection_name)

    all_chunks: list[TextChunk] = []
    for entry in log_entries:
        text = entry["content"]
        parts = chunk_text(text, chunk_size, overlap)
        for i, part in enumerate(parts):
            all_chunks.append(
                TextChunk(
                    text=part,
                    source_id=entry["id"],
                    chunk_index=i,
                    metadata={
                        "author": entry.get("author", "unknown"),
                        "category": entry.get("category", "unknown"),
                        "tags": ", ".join(entry.get("tags", [])),
                    },
                )
            )

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [c.text for c in batch]
        ids = [f"chunk_{i + j}" for j, _ in enumerate(batch)]

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        embeddings = [item.embedding for item in response.data]

        metadatas = []
        for c in batch:
            meta = {
                "source_id": c.source_id,
                "chunk_index": c.chunk_index,
                **c.metadata,
            }
            metadatas.append(meta)

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    return collection


def search(collection: chromadb.Collection, query: str, k: int = 5) -> list[dict]:
    """Search the collection and return ranked results."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
    )
    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append(
            {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i],
            }
        )
    return hits
