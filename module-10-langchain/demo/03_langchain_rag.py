"""
Demo 3: LangChain RAG — retrieval chain with ChromaDB and LCEL.
Run:  python module-10-langchain/demo/03_langchain_rag.py

DSS Pathfinder: answer crew questions by retrieving from the ship's knowledge base.

Part 1: Build the vectorstore — embed ship logs into ChromaDB via LangChain
Part 2: Build the RAG chain — retriever | format_docs | prompt | model | parser
Part 3: Interactive — ask questions with /sources and /norag comparison

Requires: OPENAI_API_KEY environment variable.
"""

import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

MODEL = "gpt-4o-mini"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS = json.loads((PROJECT_ROOT / "data" / "ship_logs.json").read_text())


# ---------------------------------------------------------------------------
# Build the vectorstore
# ---------------------------------------------------------------------------

print("Building vectorstore from ship logs...")
texts = [log["content"] for log in LOGS]
metadatas = [
    {"source": log["id"], "author": log["author"], "category": log["category"]}
    for log in LOGS
]
vectorstore = Chroma.from_texts(texts, OpenAIEmbeddings(), metadatas=metadatas)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
print(f"Indexed {len(texts)} log entries.\n")


# ---------------------------------------------------------------------------
# RAG chain
# ---------------------------------------------------------------------------

def format_docs(docs):
    return "\n\n".join(
        f"[Source {i+1}: {doc.metadata.get('source', '?')}] {doc.page_content}"
        for i, doc in enumerate(docs)
    )


rag_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are the DSS Pathfinder knowledge assistant.\n"
        "Answer using ONLY the sources below. Cite sources as [Source N].\n"
        "If the sources don't contain the answer, say so.",
    ),
    ("human", "Sources:\n{context}\n\nQuestion: {question}"),
])

model = ChatOpenAI(model=MODEL, temperature=0)
norag_model = ChatOpenAI(model=MODEL, temperature=0)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | model
    | StrOutputParser()
)

last_docs: list = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pause():
    try:
        input("\n  [Press Enter to continue...]\n")
    except (EOFError, KeyboardInterrupt):
        print()


# ---------------------------------------------------------------------------
# Part 1: Build the vectorstore
# ---------------------------------------------------------------------------

def demo_vectorstore():
    print("=" * 60)
    print("PART 1: BUILD THE VECTORSTORE")
    print("=" * 60)

    print(f"\n  Loaded {len(LOGS)} ship logs from data/ship_logs.json")
    print(f"  Embedded into ChromaDB with OpenAIEmbeddings")
    print(f"  Retriever configured for top-5 results\n")

    query = "reactor coolant"
    print(f"  Test retrieval for: '{query}'\n")
    docs = retriever.invoke(query)
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "?")
        print(f"  [{i}] {source}: {doc.page_content[:100]}...")
    print()

    print("  LangChain handles embedding + storage + search in 3 lines.")
    print("  Same as your Module 5 pipeline, but automated.")

    pause()


# ---------------------------------------------------------------------------
# Part 2: Build the RAG chain
# ---------------------------------------------------------------------------

def demo_rag_chain():
    print("=" * 60)
    print("PART 2: BUILD THE RAG CHAIN")
    print("=" * 60)

    question = "What engineering issues have been reported?"
    print(f"\n  Question: {question}\n")

    print("  Step 1: Retriever fetches relevant docs")
    docs = retriever.invoke(question)
    print(f"  → {len(docs)} documents retrieved\n")

    print("  Step 2: format_docs adds source labels")
    formatted = format_docs(docs)
    print(f"  → {formatted[:200]}...\n")

    print("  Step 3: Full chain — retrieve | format | prompt | model | parse")
    answer = rag_chain.invoke(question)
    print(f"  → {answer}\n")

    print("  The whole pipeline is one LCEL expression:")
    print('    {"context": retriever | format_docs, "question": RunnablePassthrough()}')
    print("    | prompt | model | StrOutputParser()")

    pause()


# ---------------------------------------------------------------------------
# Part 3: Interactive
# ---------------------------------------------------------------------------

def demo_interactive():
    global last_docs

    print("=" * 60)
    print("PART 3: INTERACTIVE RAG")
    print("=" * 60)

    print("\nAsk questions about the ship logs.")
    print("Commands: /sources, /norag, quit\n")

    last_question = None

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break

        if user_input == "/sources" and last_docs:
            print("\nRetrieved sources:")
            for i, doc in enumerate(last_docs, 1):
                source = doc.metadata.get("source", "?")
                author = doc.metadata.get("author", "?")
                print(f"\n  [{i}] {source} ({author})")
                print(f"      {doc.page_content[:120]}...")
            print()
            continue

        if user_input == "/norag" and last_question:
            answer = norag_model.invoke(
                [{"role": "user", "content": last_question}]
            ).content
            print(f"\nNo-RAG> {answer}\n")
            continue

        last_question = user_input
        last_docs = retriever.invoke(user_input)

        try:
            answer = rag_chain.invoke(user_input)
            print(f"\nRAG> {answer}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Build the vectorstore", demo_vectorstore),
    "2": ("Build the RAG chain",   demo_rag_chain),
    "3": ("Interactive RAG",       demo_interactive),
}


def main():
    print("\n" + "=" * 60)
    print("  DEMO 3 — LANGCHAIN RAG")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("RECAP")
    print("=" * 60)
    print()
    print("  Chroma.from_texts()   — embed and store in one call")
    print("  .as_retriever()       — turn any vectorstore into a retriever")
    print("  retriever | format    — LCEL wires retrieval into the chain")
    print("  /norag                — compare to see how grounding helps")
    print("=" * 60)


if __name__ == "__main__":
    main()
