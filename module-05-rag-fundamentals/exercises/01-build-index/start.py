"""
Exercise 1: Build the Index
=============================
Load ship logs, chunk them, embed into ChromaDB, and search interactively.

Run:  python start.py
"""

import json
from pathlib import Path

# TODO: import chromadb
# TODO: import OpenAI from openai

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ship_logs.json"


def load_logs() -> list[dict]:
    """Load ship logs from the data directory."""
    return json.loads(DATA_PATH.read_text())


# TODO: Implement chunk_text(text, chunk_size, overlap) -> list[str]
#   Split text into overlapping windows of chunk_size characters.
#   Each window overlaps the previous by `overlap` characters.
#   Return a list of strings.


# TODO: Implement build_index(log_entries) -> chromadb.Collection
#   1. Create a ChromaDB client and collection
#   2. For each log entry, chunk the content
#   3. Embed all chunks using OpenAI text-embedding-3-small
#   4. Add to the collection with metadata (source_id, chunk_index, author, category)
#   5. Return the collection


# TODO: Implement search(collection, query, k) -> list[dict]
#   1. Query the collection with query_texts=[query], n_results=k
#   2. Return a list of dicts with keys: id, text, source, distance, metadata


def main():
    print("Loading ship logs...")
    logs = load_logs()
    print(f"Loaded {len(logs)} logs.")

    # TODO: Build the index
    # collection = build_index(logs)
    # print(f"Index ready. {collection.count()} chunks indexed.")

    # TODO: Interactive search loop
    #   - Plain text -> search and display results
    #   - /stats -> show collection.count() and source info
    #   - /chunk <id> -> collection.get(ids=[id])
    #   - /similar <id> -> get chunk text, then query with it
    #   - quit -> break

    print("TODO: implement build_index and search, then uncomment the loop.")


if __name__ == "__main__":
    main()
