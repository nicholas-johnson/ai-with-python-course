"""
Exercise 3: RAG MCP Server -- solution_server.py
===================================================
Complete FastMCP server wrapping the RAG pipeline.

Run standalone:  python -m mcp dev solution_server.py
"""

import json

from mcp.server.fastmcp import FastMCP

from index_builder import load_logs, build_index, search
from rag_utils import rag_chat

mcp = FastMCP("RAG Server")

print("RAG Server: loading logs and building index...", flush=True)
logs = load_logs()
collection = build_index(logs)
print(f"RAG Server: index ready ({collection.count()} chunks)", flush=True)


@mcp.tool()
def search_docs(query: str, k: int = 5) -> str:
    """Search the document index for relevant passages."""
    hits = search(collection, query, k)
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
    answer, passages = rag_chat(question, collection)
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
