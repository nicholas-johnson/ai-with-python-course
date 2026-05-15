"""
Exercise 2: RAG Chat
======================
Grounded chat with citations using the index from Exercise 1.

Run:  python start.py
"""

import json
from dataclasses import dataclass
from pathlib import Path

import chromadb
from openai import OpenAI

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ship_logs.json"
client = OpenAI()


# ---------------------------------------------------------------------------
# From Exercise 01 — index builder (complete)
# ---------------------------------------------------------------------------

@dataclass
class TextChunk:
    text: str
    source_id: str
    chunk_index: int
    metadata: dict


def load_logs() -> list[dict]:
    return json.loads(DATA_PATH.read_text())


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
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
    chroma = chromadb.Client()
    try:
        chroma.delete_collection(collection_name)
    except Exception:
        pass
    collection = chroma.create_collection(collection_name)

    all_chunks: list[TextChunk] = []
    for entry in log_entries:
        parts = chunk_text(entry["content"], chunk_size, overlap)
        for i, part in enumerate(parts):
            all_chunks.append(TextChunk(
                text=part,
                source_id=entry["id"],
                chunk_index=i,
                metadata={
                    "author": entry.get("author", "unknown"),
                    "category": entry.get("category", "unknown"),
                    "tags": ", ".join(entry.get("tags", [])),
                },
            ))

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [c.text for c in batch]
        ids = [f"chunk_{i + j}" for j, _ in enumerate(batch)]
        response = client.embeddings.create(model="text-embedding-3-small", input=texts)
        embeddings = [item.embedding for item in response.data]
        metadatas = [{"source_id": c.source_id, "chunk_index": c.chunk_index, **c.metadata} for c in batch]
        collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)

    return collection


def search(collection: chromadb.Collection, query: str, k: int = 5) -> list[dict]:
    response = client.embeddings.create(model="text-embedding-3-small", input=[query])
    query_embedding = response.data[0].embedding
    results = collection.query(query_embeddings=[query_embedding], n_results=k)
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "distance": results["distances"][0][i],
            "metadata": results["metadatas"][0][i],
        })
    return hits


# ---------------------------------------------------------------------------
# TODO: Implement build_grounded_prompt(query, passages) -> list[dict]
#   Build a system + user message pair where:
#   - system: instructs the LLM to answer ONLY from the sources, citing [Source N]
#   - user: contains the source texts labeled [Source 1: LOG-XXX] ... [Source N: ...]
#           followed by "Question: <query>"
#   Return a list of message dicts [{"role": ..., "content": ...}, ...]
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO: Implement rag_chat(query, collection, k) -> tuple[str, list[dict]]
#   1. Call search(collection, query, k) to get passages
#   2. Call build_grounded_prompt(query, passages) to get messages
#   3. Call client.chat.completions.create(model="gpt-4o-mini", messages=messages)
#   4. Return (answer_text, passages)
# ---------------------------------------------------------------------------


def main():
    print("Loading ship logs and building index...")
    logs = load_logs()
    # TODO: Build the index
    # collection = build_index(logs)
    # print(f"RAG Chat ready. {collection.count()} chunks indexed.\n")

    # TODO: Interactive loop
    #   Store last_query and last_passages for /sources, /norag, /prompt commands
    #   - Plain text -> rag_chat(), print answer + brief source list
    #   - /sources -> show full text of last_passages
    #   - /norag -> re-ask last_query directly (no retrieval)
    #   - /k <n> -> change retrieval count
    #   - /prompt -> show the full grounded prompt
    #   - quit -> break

    print("TODO: implement build_grounded_prompt and rag_chat, then uncomment the loop.")


if __name__ == "__main__":
    main()
