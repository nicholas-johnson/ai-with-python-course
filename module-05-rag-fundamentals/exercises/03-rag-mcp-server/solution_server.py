"""
Exercise 3: RAG MCP Server -- solution_server.py
===================================================
Complete FastMCP server wrapping the RAG pipeline.

Run standalone:  python -m mcp dev solution_server.py
"""

import json
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from mcp.server.fastmcp import FastMCP

load_dotenv()

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "scout_logs.json"
client = OpenAI()
mcp = FastMCP("RAG Server")


# --- Index builder from Exercise 01 ---

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
    collection_name: str = "scout_logs",
) -> chromadb.Collection:
    chroma = chromadb.Client()
    try:
        chroma.delete_collection(collection_name)
    except ValueError:
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


# --- RAG chat from Exercise 02 ---

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


# --- Lazy index init ---

_collection = None


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        print("RAG Server: loading logs and building index...", flush=True)
        logs = load_logs()
        _collection = build_index(logs)
        print(f"RAG Server: index ready ({_collection.count()} chunks)", flush=True)
    return _collection


# --- MCP tools ---

@mcp.tool()
def search_docs(query: str, k: int = 5) -> str:
    """Search the document index for relevant passages."""
    hits = search(_get_collection(), query, k)
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
        result = _get_collection().get(ids=[chunk_id])
        if result["documents"]:
            meta = result["metadatas"][0]
            return json.dumps({
                "chunk_id": chunk_id,
                "source_id": meta.get("source_id", "unknown"),
                "chunk_index": meta.get("chunk_index", "?"),
                "author": meta.get("author", "unknown"),
                "category": meta.get("category", "unknown"),
                "text": result["documents"][0],
            }, indent=2)
        return f"Chunk '{chunk_id}' not found."
    except Exception as e:
        return f"Error retrieving chunk: {e}"


@mcp.tool()
def ask_docs(question: str) -> str:
    """Ask a question and get a RAG-generated answer with citations."""
    answer, passages = rag_chat(question, _get_collection())
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
    all_meta = _get_collection().get()["metadatas"]
    source_ids = sorted({m["source_id"] for m in all_meta})
    return "\n".join(f"- {sid}" for sid in source_ids)


if __name__ == "__main__":
    mcp.run()
