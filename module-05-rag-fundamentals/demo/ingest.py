"""
Module 5 Demo — ingest.py
===========================
Load ship logs, chunk, embed with OpenAI, and store in ChromaDB.

Requires:
  - ChromaDB running via docker compose (port 8100)
  - OPENAI_API_KEY environment variable

Usage:
  python ingest.py              # ingest (skip if collection exists)
  python ingest.py --reset      # wipe and rebuild
  python ingest.py --chunk-size 300 --overlap 30
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import chromadb
from openai import OpenAI

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ship_logs.json"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8100
COLLECTION_NAME = "ship_logs"


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


def ingest(chunk_size: int = 500, overlap: int = 50, reset: bool = False):
    """Load logs, chunk, embed, and store in ChromaDB."""
    client = OpenAI()
    chroma = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    if reset:
        try:
            chroma.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing '{COLLECTION_NAME}' collection.")
        except Exception:
            pass

    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    if collection.count() > 0 and not reset:
        print(f"  Collection '{COLLECTION_NAME}' already has {collection.count()} chunks.")
        print("  Use --reset to wipe and rebuild.")
        return collection

    # Load
    logs = load_logs()
    print(f"  Loaded {len(logs)} ship logs from {DATA_PATH.name}")

    # Chunk
    all_chunks: list[TextChunk] = []
    for entry in logs:
        parts = chunk_text(entry["content"], chunk_size, overlap)
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
    print(f"  Created {len(all_chunks)} chunks (size={chunk_size}, overlap={overlap})")

    # Embed + store in batches
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

        metadatas = [
            {
                "source_id": c.source_id,
                "chunk_index": c.chunk_index,
                **c.metadata,
            }
            for c in batch
        ]

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"  Stored batch {i // batch_size + 1} ({len(batch)} chunks)")

    print(f"\n  Done. Collection '{COLLECTION_NAME}' now has {collection.count()} chunks.")
    return collection


def main():
    parser = argparse.ArgumentParser(description="Ingest ship logs into ChromaDB")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=50, help="Overlap between chunks")
    parser.add_argument("--reset", action="store_true", help="Wipe and rebuild the collection")
    args = parser.parse_args()

    print("=" * 50)
    print("  Module 5 Demo — Ingest")
    print("=" * 50)
    print()

    ingest(chunk_size=args.chunk_size, overlap=args.overlap, reset=args.reset)


if __name__ == "__main__":
    main()
