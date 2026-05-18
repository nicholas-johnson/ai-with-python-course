"""
Module 5 Demo — server.py
============================
FastMCP server that exposes RAG tools over a persistent ChromaDB collection.

The collection must already be populated by ingest.py.

Usage:
  python server.py                  # stdio transport (for agent.py)
  python -m mcp dev server.py       # MCP Inspector web UI

Requires:
  - ChromaDB running via docker compose (port 8100)
  - OPENAI_API_KEY environment variable
"""

import json

import chromadb
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import OpenAI

load_dotenv()

CHROMA_HOST = "localhost"
CHROMA_PORT = 8100
COLLECTION_NAME = "ship_logs"

mcp = FastMCP("RAG Server")
openai_client = OpenAI()
chroma = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma.get_or_create_collection(COLLECTION_NAME)

print(f"RAG Server: connected to ChromaDB, collection has {collection.count()} chunks", flush=True)


def _embed(text: str) -> list[float]:
    """Embed a single text string."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=[text],
    )
    return response.data[0].embedding


def _search(query: str, k: int = 5) -> list[dict]:
    """Vector search over the collection."""
    query_embedding = _embed(query)
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


def _rag_answer(question: str, k: int = 5) -> tuple[str, list[dict]]:
    """Full RAG: retrieve, ground, generate."""
    passages = _search(question, k)

    context_parts = []
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        context_parts.append(f"[Source {i}: {source}] {p['text']}")

    messages = [
        {
            "role": "system",
            "content": (
                "Answer the question using ONLY the sources below. "
                "Cite sources using [Source N]. "
                "If the sources don't contain the answer, say so."
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(context_parts) + f"\n\nQuestion: {question}",
        },
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    return response.choices[0].message.content, passages


@mcp.tool()
def search_docs(query: str, k: int = 5) -> str:
    """Search the document index for relevant passages."""
    hits = _search(query, k)
    lines = []
    for hit in hits:
        source = hit["metadata"].get("source_id", "?")
        score = 1 - hit["distance"]
        preview = hit["text"][:200].replace("\n", " ")
        lines.append(f"[{score:.2f}] {hit['id']} ({source}): {preview}")
    return "\n".join(lines) if lines else "No results found."


@mcp.tool()
def get_chunk(chunk_id: str) -> str:
    """Retrieve the full text of a specific chunk by ID."""
    try:
        result = collection.get(ids=[chunk_id])
        if result["documents"]:
            meta = result["metadatas"][0]
            return json.dumps(
                {
                    "chunk_id": chunk_id,
                    "source_id": meta.get("source_id", "unknown"),
                    "chunk_index": meta.get("chunk_index", "?"),
                    "author": meta.get("author", "unknown"),
                    "category": meta.get("category", "unknown"),
                    "text": result["documents"][0],
                },
                indent=2,
            )
        return f"Chunk '{chunk_id}' not found."
    except Exception as e:
        return f"Error retrieving chunk: {e}"


@mcp.tool()
def ask_docs(question: str) -> str:
    """Ask a question and get a RAG-generated answer with citations."""
    answer, passages = _rag_answer(question)
    source_lines = []
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        preview = p["text"][:100].replace("\n", " ")
        source_lines.append(f"  [Source {i}: {source}] {preview}...")
    sources_text = "\n".join(source_lines)
    return f"{answer}\n\nSources used:\n{sources_text}"


@mcp.tool()
def list_sources() -> str:
    """List all source document IDs in the index."""
    all_meta = collection.get()["metadatas"]
    source_ids = sorted({m["source_id"] for m in all_meta})
    return "\n".join(f"- {sid}" for sid in source_ids)


if __name__ == "__main__":
    mcp.run()
