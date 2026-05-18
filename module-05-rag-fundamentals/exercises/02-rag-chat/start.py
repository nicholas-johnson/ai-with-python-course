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
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "scout_logs.json"
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
    collection_name: str = "scout_logs",
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

def build_grounded_prompt(query: str, passages: list[dict]) -> list[dict]:
    raise NotImplementedError("TODO: build system + user messages from query and passages")


# ---------------------------------------------------------------------------
# TODO: Implement rag_chat(query, collection, k) -> tuple[str, list[dict]]
#   1. Call search(collection, query, k) to get passages
#   2. Call build_grounded_prompt(query, passages) to get messages
#   3. Call client.chat.completions.create(model="gpt-4o-mini", messages=messages)
#   4. Return (answer_text, passages)
# ---------------------------------------------------------------------------

def rag_chat(query: str, collection, k: int = 5) -> tuple[str, list[dict]]:
    raise NotImplementedError("TODO: search, build prompt, call LLM, return answer + passages")


# ---------------------------------------------------------------------------
# Display and slash-command helpers (complete)
# ---------------------------------------------------------------------------

def display_sources(passages: list[dict], brief: bool = False):
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        if brief:
            preview = p["text"][:80].replace("\n", " ")
            print(f'    [{i}] {source}: "{preview}..."')
        else:
            print(f"\n  [Source {i}: {source}]")
            print(f"  {p['text']}")


def handle_sources_command(last_passages: list[dict] | None):
    """Show full text of the passages retrieved in the last query."""
    if last_passages:
        print("\n  === Retrieved Sources ===")
        display_sources(last_passages)
        print()
    else:
        print("  No previous query. Ask a question first.")


def handle_norag_command(client: OpenAI, last_query: str | None):
    """Re-ask the last question without retrieval augmentation."""
    if last_query:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": last_query}],
        )
        print(f"  (No RAG) {response.choices[0].message.content}\n")
    else:
        print("  No previous query. Ask a question first.")


def handle_k_command(cmd_args: str) -> int:
    """Parse and return a new retrieval-k value, or -1 on bad input."""
    try:
        new_k = int(cmd_args)
        print(f"  Retrieval set to {new_k} chunks.\n")
        return new_k
    except ValueError:
        print("  Usage: /k <number>")
        return -1


def handle_prompt_command(last_messages: list[dict] | None):
    """Display the full grounded prompt sent to the LLM."""
    if last_messages:
        print("\n  === Grounded Prompt ===")
        for msg in last_messages:
            print(f"  [{msg['role']}]")
            for line in msg["content"].split("\n"):
                print(f"    {line}")
        print()
    else:
        print("  No previous query. Ask a question first.")


def main():
    print("Loading scout logs and building index...")
    logs = load_logs()
    collection = build_index(logs)
    print(f"RAG Chat ready. {collection.count()} chunks indexed.")
    print("Ask a question, or type a command (/sources, /norag, /k <n>, /prompt), or 'quit'.\n")

    k = 5
    last_query = None
    last_passages = None
    last_messages = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break

        if user_input == "/sources":
            handle_sources_command(last_passages)
            continue

        if user_input == "/norag":
            handle_norag_command(client, last_query)
            continue

        if user_input.startswith("/k "):
            new_k = handle_k_command(user_input.split(" ", 1)[1])
            if new_k > 0:
                k = new_k
            continue

        if user_input == "/prompt":
            handle_prompt_command(last_messages)
            continue

        last_query = user_input
        answer, last_passages = rag_chat(user_input, collection, k)
        last_messages = build_grounded_prompt(user_input, last_passages)
        print(f"Agent: {answer}")
        print("\n  Sources:")
        display_sources(last_passages, brief=True)
        print()


if __name__ == "__main__":
    main()
