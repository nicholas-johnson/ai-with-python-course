"""
Exercise 1 -- Solution
========================
Load scout logs, chunk, embed into ChromaDB, and search interactively.

Run:  python solution.py
"""

import json
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "scout_logs.json"
client = OpenAI()


@dataclass
class TextChunk:
    text: str
    source_id: str
    chunk_index: int
    metadata: dict


def load_logs() -> list[dict]:
    """Load scout logs from the data directory."""
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
    collection_name: str = "scout_logs",
) -> chromadb.Collection:
    """Chunk all logs, embed with OpenAI, and store in ChromaDB."""
    chroma = chromadb.Client()

    try:
        chroma.delete_collection(collection_name)
    except ValueError:
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


def display_results(hits: list[dict]):
    """Print search results in a readable format."""
    for hit in hits:
        source = hit["metadata"].get("source_id", "?")
        score = 1 - hit["distance"]  # cosine distance -> similarity
        preview = hit["text"][:120].replace("\n", " ")
        print(f"  [{score:.2f}] {hit['id']} ({source}): \"{preview}...\"")


def print_collection_stats(collection: chromadb.Collection):
    """Display summary statistics for the indexed collection."""
    count = collection.count()
    all_meta = collection.get()["metadatas"]
    sources = {m["source_id"] for m in all_meta}
    avg_len = sum(len(d) for d in collection.get()["documents"]) / max(count, 1)
    print(f"  Collection: scout_logs | {count} chunks | avg {avg_len:.0f} chars | {len(sources)} source logs")


def show_chunk_by_id(collection: chromadb.Collection, chunk_id: str):
    """Retrieve and display a single chunk by its ID."""
    try:
        result = collection.get(ids=[chunk_id])
        if result["documents"]:
            meta = result["metadatas"][0]
            print(f"  Source: {meta.get('source_id', '?')} | Index: {meta.get('chunk_index', '?')}")
            print(f"  Author: {meta.get('author', '?')} | Category: {meta.get('category', '?')}")
            print(f"  \"{result['documents'][0]}\"")
        else:
            print(f"  Chunk '{chunk_id}' not found.")
    except Exception as e:
        print(f"  Error: {e}")


def show_similar_chunks(collection: chromadb.Collection, chunk_id: str, k: int = 5):
    """Find and display chunks similar to the given chunk."""
    try:
        result = collection.get(ids=[chunk_id])
        if result["documents"]:
            hits = search(collection, result["documents"][0], k=k)
            filtered = [h for h in hits if h["id"] != chunk_id]
            display_results(filtered)
        else:
            print(f"  Chunk '{chunk_id}' not found.")
    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("Loading scout logs...")
    logs = load_logs()
    print(f"Loaded {len(logs)} logs. Chunking and embedding...")

    collection = build_index(logs)
    print(f"Index ready. {collection.count()} chunks indexed.\n")
    print("Type a query, or a command (/stats, /chunk <id>, /similar <id>), or 'quit'.\n")

    while True:
        try:
            user_input = input("Search: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/stats":
            print_collection_stats(collection)
            continue

        if user_input.startswith("/chunk "):
            chunk_id = user_input.split(" ", 1)[1].strip()
            show_chunk_by_id(collection, chunk_id)
            continue

        if user_input.startswith("/similar "):
            chunk_id = user_input.split(" ", 1)[1].strip()
            show_similar_chunks(collection, chunk_id)
            continue

        hits = search(collection, user_input)
        display_results(hits)
        print()


if __name__ == "__main__":
    main()
