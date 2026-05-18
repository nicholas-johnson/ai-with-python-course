"""
Exercise 1: Build the Index
=============================
Load scout logs, chunk them, embed into ChromaDB, and search interactively.

Run:  python start.py
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
    raise NotImplementedError("TODO: split text into overlapping chunks")


def build_index(
    log_entries: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
    collection_name: str = "scout_logs",
) -> chromadb.Collection:
    """Chunk all logs, embed with OpenAI, and store in ChromaDB."""
    raise NotImplementedError("TODO: chunk, embed, and store in ChromaDB")


def search(collection: chromadb.Collection, query: str, k: int = 5) -> list[dict]:
    """Search the collection and return ranked results."""
    raise NotImplementedError("TODO: embed query and search collection")


def display_results(hits: list[dict]):
    """Print search results in a readable format."""
    for hit in hits:
        source = hit["metadata"].get("source_id", "?")
        score = 1 - hit["distance"]
        preview = hit["text"][:120].replace("\n", " ")
        print(f"  [{score:.2f}] {hit['id']} ({source}): \"{preview}...\"")


def print_collection_stats(collection: chromadb.Collection):
    """Display summary statistics for the indexed collection."""
    raise NotImplementedError("TODO: print chunk count, avg length, source count")


def show_chunk_by_id(collection: chromadb.Collection, chunk_id: str):
    """Retrieve and display a single chunk by its ID."""
    raise NotImplementedError("TODO: fetch chunk by ID and print metadata + text")


def show_similar_chunks(collection: chromadb.Collection, chunk_id: str, k: int = 5):
    """Find and display chunks similar to the given chunk."""
    raise NotImplementedError("TODO: get chunk text, search for similar, display results")


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
