"""
Exercise 2: RAG Chat
======================
Grounded chat with citations using the index from Exercise 1.

Run:  python start.py
"""

from index_builder import load_logs, build_index, search

# TODO: import OpenAI from openai

# TODO: create the OpenAI client


# TODO: Implement build_grounded_prompt(query, passages) -> list[dict]
#   Build a system + user message pair where:
#   - system: instructs the LLM to answer ONLY from the sources, citing [Source N]
#   - user: contains the source texts labeled [Source 1: LOG-XXX] ... [Source N: ...]
#           followed by "Question: <query>"
#   Return a list of message dicts [{"role": ..., "content": ...}, ...]


# TODO: Implement rag_chat(query, collection, k) -> tuple[str, list[dict]]
#   1. Call search(collection, query, k) to get passages
#   2. Call build_grounded_prompt(query, passages) to get messages
#   3. Call OpenAI chat.completions.create(model="gpt-4o-mini", messages=messages)
#   4. Return (answer_text, passages)


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
