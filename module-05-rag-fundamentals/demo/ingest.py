"""
Module 5 Demo — ingest.py
===========================
Load ship logs, chunk, embed with OpenAI, and store in ChromaDB.

Requires:
  - OPENAI_API_KEY environment variable

Usage:
  python ingest.py
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ship_logs.json"
CHROMA_PATH = str(Path(__file__).resolve().parent / "chroma_data")
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


def ingest(chunk_size: int = 500, overlap: int = 50):
    """Load logs, chunk, embed, and store in ChromaDB."""
    client = OpenAI()

    chroma_path = Path(CHROMA_PATH)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
        print("  Cleared previous embeddings.\n")

    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )

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
    print(f"  Created {len(all_chunks)} chunks (size={chunk_size}, overlap={overlap})\n")

    for i, chunk in enumerate(all_chunks):
        header = f"  [{chunk.source_id} #{chunk.chunk_index}]"
        preview = chunk.text[:80].replace("\n", " ")
        print(f"  {header} {preview}...")
    print()

    # Embed + store in batches
    batch_size = 20
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


def prompt_params() -> tuple[int, int]:
    """Interactive menu to configure chunk parameters."""
    print("  Chunking parameters:")
    print("  --------------------")
    print(f"  [1] chunk_size=50,  overlap=5   (too small — fragments lose meaning)")
    print(f"  [2] chunk_size=100, overlap=10  (too small — splits mid-sentence)")
    print(f"  [3] chunk_size=300, overlap=30  (small, high granularity)")
    print(f"  [4] chunk_size=500, overlap=50  (default, good balance)")
    print(f"  [5] chunk_size=800, overlap=100 (large, more context per chunk)")
    print(f"  [6] Custom")
    print()

    choice = input("  Choose [1-6] (default: 4): ").strip()

    if choice == "1":
        return 50, 5
    elif choice == "2":
        return 100, 10
    elif choice == "3":
        return 300, 30
    elif choice == "5":
        return 800, 100
    elif choice == "6":
        try:
            cs = int(input("  chunk_size: ").strip())
            ov = int(input("  overlap: ").strip())
            return cs, ov
        except ValueError:
            print("  Invalid input, using defaults.")
            return 500, 50
    else:
        return 500, 50


def main():
    print("=" * 50)
    print("  Module 5 Demo — Ingest")
    print("=" * 50)
    print()

    chunk_size, overlap = prompt_params()
    print(f"\n  Using chunk_size={chunk_size}, overlap={overlap}\n")

    ingest(chunk_size=chunk_size, overlap=overlap)


if __name__ == "__main__":
    main()
