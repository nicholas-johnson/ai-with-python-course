"""
Module 5 Demo — query.py
===========================
Interactive query REPL for the vector database. Use after running ingest.py.

Shows similarity scores and chunk content for each query, making it easy
to demonstrate how retrieval quality changes with different chunk sizes.

Usage:
  python query.py
"""

from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CHROMA_PATH = str(Path(__file__).resolve().parent / "chroma_data")
COLLECTION_NAME = "ship_logs"


def main():
    client = OpenAI()
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = chroma.get_collection(COLLECTION_NAME, embedding_function=None)
    except Exception:
        print("  No collection found. Run ingest.py first.")
        return

    count = collection.count()
    all_meta = collection.get()["metadatas"]
    sources = sorted({m["source_id"] for m in all_meta})

    print("=" * 50)
    print("  Module 5 Demo — Query")
    print("=" * 50)
    print(f"\n  Collection: {COLLECTION_NAME}")
    print(f"  Chunks: {count}")
    print(f"  Sources: {len(sources)}")
    print()
    print("  Commands:")
    print("    <query>        — search the index")
    print("    /chunk <id>    — show full chunk text")
    print("    /sources       — list all source document IDs")
    print("    /stats         — show collection stats")
    print("    /k <number>    — change number of results (default: 5)")
    print("    quit           — exit")
    print()

    k = 5

    while True:
        try:
            user_input = input("Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/sources":
            for sid in sources:
                print(f"  - {sid}")
            print()
            continue

        if user_input == "/stats":
            avg_len = sum(len(d) for d in collection.get()["documents"]) / max(count, 1)
            print(f"  Collection: {COLLECTION_NAME}")
            print(f"  Chunks: {count}")
            print(f"  Avg chunk length: {avg_len:.0f} chars")
            print(f"  Sources: {len(sources)}")
            print(f"  Current k: {k}")
            print()
            continue

        if user_input.startswith("/k "):
            try:
                k = int(user_input.split(" ", 1)[1].strip())
                print(f"  Now showing top {k} results.\n")
            except ValueError:
                print("  Usage: /k <number>\n")
            continue

        if user_input.startswith("/chunk "):
            chunk_id = user_input.split(" ", 1)[1].strip()
            try:
                result = collection.get(ids=[chunk_id])
                if result["documents"]:
                    meta = result["metadatas"][0]
                    print(f"\n  ID: {chunk_id}")
                    print(f"  Source: {meta.get('source_id', '?')}")
                    print(f"  Author: {meta.get('author', '?')}")
                    print(f"  Category: {meta.get('category', '?')}")
                    print(f"  Tags: {meta.get('tags', '')}")
                    print(f"  ---")
                    print(f"  {result['documents'][0]}")
                else:
                    print(f"  Chunk '{chunk_id}' not found.")
            except Exception as e:
                print(f"  Error: {e}")
            print()
            continue

        # Vector search
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[user_input],
        )
        query_embedding = response.data[0].embedding

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )

        if not results["ids"][0]:
            print("  No results found.\n")
            continue

        print()
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            text = results["documents"][0][i]
            distance = results["distances"][0][i]
            meta = results["metadatas"][0][i]
            score = 1 - distance

            source = meta.get("source_id", "?")
            author = meta.get("author", "?")

            print(f"  [{score:.3f}] {chunk_id} ({source}, {author})")
            print(f"         \"{text}\"")
            print()

        print(f"  ({len(results['ids'][0])} results)\n")


if __name__ == "__main__":
    main()
