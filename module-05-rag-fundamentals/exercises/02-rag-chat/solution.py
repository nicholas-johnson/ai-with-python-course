"""
Exercise 2 -- Solution
========================
RAG Chat with citations, built on the Exercise 1 index.

Run:  python solution.py
"""

from index_builder import load_logs, build_index, search
from openai import OpenAI

client = OpenAI()


def build_grounded_prompt(query: str, passages: list[dict]) -> list[dict]:
    """Construct a grounded prompt with [Source N] labels."""
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


def rag_chat(query: str, collection, k: int = 5) -> tuple[str, list[dict]]:
    """Retrieve relevant chunks, build a grounded prompt, and generate an answer."""
    passages = search(collection, query, k)
    messages = build_grounded_prompt(query, passages)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    answer = response.choices[0].message.content
    return answer, passages


def display_sources(passages: list[dict], brief: bool = False):
    """Print source passages."""
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        if brief:
            preview = p["text"][:80].replace("\n", " ")
            print(f"    [{i}] {source}: \"{preview}...\"")
        else:
            print(f"\n  [Source {i}: {source}]")
            print(f"  {p['text']}")


def main():
    print("Loading ship logs and building index...")
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
            print("Goodbye!")
            break

        if user_input == "/sources":
            if last_passages:
                print("\n  === Retrieved Sources ===")
                display_sources(last_passages, brief=False)
                print()
            else:
                print("  No previous query. Ask a question first.")
            continue

        if user_input == "/norag":
            if last_query:
                print("  (Without RAG)")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": last_query}],
                )
                print(f"  {response.choices[0].message.content}\n")
            else:
                print("  No previous query. Ask a question first.")
            continue

        if user_input.startswith("/k "):
            try:
                k = int(user_input.split(" ", 1)[1])
                print(f"  Retrieval set to {k} chunks.\n")
            except ValueError:
                print("  Usage: /k <number>")
            continue

        if user_input == "/prompt":
            if last_messages:
                print("\n  === Grounded Prompt ===")
                for msg in last_messages:
                    print(f"  [{msg['role']}]")
                    for line in msg["content"].split("\n"):
                        print(f"    {line}")
                print()
            else:
                print("  No previous query. Ask a question first.")
            continue

        last_query = user_input
        last_passages = search(collection, user_input, k)
        last_messages = build_grounded_prompt(user_input, last_passages)

        answer, _ = rag_chat(user_input, collection, k)
        print(f"Agent: {answer}")
        print("\n  Sources:")
        display_sources(last_passages, brief=True)
        print()


if __name__ == "__main__":
    main()
