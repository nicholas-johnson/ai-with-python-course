"""
Exercise 3: RAG MCP Server -- server.py
==========================================
A FastMCP server that wraps the RAG pipeline as discoverable tools.

Run standalone:  python -m mcp dev server.py
"""

import json
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from mcp.server.fastmcp import FastMCP

load_dotenv()

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ship_logs.json"
client = OpenAI()
mcp = FastMCP("RAG Server")


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


def search(collection_ref: chromadb.Collection, query: str, k: int = 5) -> list[dict]:
    response = client.embeddings.create(model="text-embedding-3-small", input=[query])
    query_embedding = response.data[0].embedding
    results = collection_ref.query(query_embeddings=[query_embedding], n_results=k)
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
# From Exercise 02 — RAG chat (complete)
# ---------------------------------------------------------------------------

def build_grounded_prompt(query: str, passages: list[dict]) -> list[dict]:
    context_parts = []
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        context_parts.append(f"[Source {i}: {source}] {p['text']}")

    system = (
        "Answer the question using ONLY the sources below. "
        "Cite sources using [Source N]. "
        "If the sources don't contain the answer, say so."
    )
    context = "\n\n".join(context_parts)
    user_msg = f"{context}\n\nQuestion: {query}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]


def rag_chat(query: str, collection_ref, k: int = 5) -> tuple[str, list[dict]]:
    passages = search(collection_ref, query, k)
    messages = build_grounded_prompt(query, passages)
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content, passages


# ---------------------------------------------------------------------------
# TODO: Build the index at module level
# ---------------------------------------------------------------------------

# logs = load_logs()
# collection = build_index(logs)


# ---------------------------------------------------------------------------
# TODO: Implement MCP tools
# ---------------------------------------------------------------------------

# @mcp.tool()
# def search_docs(query: str, k: int = 5) -> str:
#     """Search the document index for relevant passages."""
#     hits = search(collection, query, k)
#     ... format hits as readable text ...

# @mcp.tool()
# def get_chunk(chunk_id: str) -> str:
#     """Retrieve the full text of a specific chunk by ID."""
#     ...

# @mcp.tool()
# def ask_docs(question: str) -> str:
#     """Ask a question and get a RAG-generated answer with citations."""
#     answer, passages = rag_chat(question, collection)
#     ...

# @mcp.tool()
# def list_sources() -> str:
#     """List all source document IDs in the index."""
#     ...


if __name__ == "__main__":
    mcp.run()
