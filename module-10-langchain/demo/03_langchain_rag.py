"""
Demo 3: LangChain RAG — retrieval chain with ChromaDB and LCEL.
Run:  python module-10-langchain/demo/03_langchain_rag.py

DSS Pathfinder: answer crew questions by retrieving from the ship's knowledge base.

Part 1: Build the vectorstore — embed ship logs into ChromaDB via LangChain
Part 2: Build the RAG chain — returns the answer *and* the docs it used
Part 3: Agentic RAG — the retriever as a tool for create_agent
Part 4: Interactive — ask questions with /sources, /norag, and /agent comparison

Requires: OPENAI_API_KEY environment variable.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
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

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)
norag_model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)

answer_chain = (
    RunnablePassthrough.assign(context=lambda x: format_docs(x["docs"]))
    | rag_prompt
    | model
    | StrOutputParser()
)

# invoke(question) -> {"question", "docs", "answer"}: one retrieval, answer + sources
rag_chain = (
    {"docs": retriever, "question": RunnablePassthrough()}
    | RunnablePassthrough.assign(answer=answer_chain)
)


# ---------------------------------------------------------------------------
# Agentic RAG
# ---------------------------------------------------------------------------

@tool
def search_logs(query: str) -> str:
    """Search the DSS Pathfinder ship logs. Use for questions about past events or incidents."""
    return format_docs(retriever.invoke(query))


rag_agent = create_agent(
    model,
    [search_logs],
    system_prompt=(
        "You are the DSS Pathfinder knowledge assistant. Search the ship logs when a "
        "question needs them — rephrase or search more than once if the first results "
        "miss. Cite sources as [Source N: id]."
    ),
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

    print("  Step 3: Full chain — retrieve, then assign the answer")
    result = rag_chain.invoke(question)
    print(f"  → keys: {sorted(result)}")
    print(f"  → answer: {result['answer']}\n")

    print("  The whole pipeline is one LCEL expression:")
    print('    {"docs": retriever, "question": RunnablePassthrough()}')
    print("    | RunnablePassthrough.assign(answer=answer_chain)")
    print("  .assign() keeps the docs in the output, so you can show sources")
    print("  without retrieving a second time.")

    pause()


# ---------------------------------------------------------------------------
# Part 3: Agentic RAG
# ---------------------------------------------------------------------------

def demo_agentic_rag():
    print("=" * 60)
    print("PART 3: AGENTIC RAG")
    print("=" * 60)

    print("\n  A chain always retrieves once, with the user's exact words.")
    print("  Wrap the retriever as a tool and an agent decides when and what to search.\n")

    question = "Have there been any problems with life support or the medical bay?"
    print(f"  Question: {question}\n")
    result = rag_agent.invoke({"messages": [{"role": "user", "content": question}]})
    for msg in result["messages"]:
        if msg.type == "ai" and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"  → {call['name']}({json.dumps(call['args'])})")
    print(f"\n  Answer: {result['messages'][-1].text}\n")

    print("  Trade-off: more flexible, but more model calls (cost + latency).")
    pause()


# ---------------------------------------------------------------------------
# Part 4: Interactive
# ---------------------------------------------------------------------------

def demo_interactive():
    global last_docs

    print("=" * 60)
    print("PART 4: INTERACTIVE RAG")
    print("=" * 60)

    print("\nAsk questions about the ship logs.")
    print("Commands: /sources, /norag, /agent, quit\n")

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
            ).text
            print(f"\nNo-RAG> {answer}\n")
            continue

        if user_input == "/agent" and last_question:
            result = rag_agent.invoke({"messages": [{"role": "user", "content": last_question}]})
            print(f"\nAgent> {result['messages'][-1].text}\n")
            continue

        last_question = user_input

        try:
            result = rag_chain.invoke(user_input)
            last_docs = result["docs"]
            print(f"\nRAG> {result['answer']}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Build the vectorstore", demo_vectorstore),
    "2": ("Build the RAG chain",   demo_rag_chain),
    "3": ("Agentic RAG",           demo_agentic_rag),
    "4": ("Interactive RAG",       demo_interactive),
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
    print("  .assign(answer=...)   — answer + sources from one retrieval")
    print("  @tool search_logs     — agentic RAG: the agent decides when to search")
    print("  /norag                — compare to see how grounding helps")
    print("=" * 60)


if __name__ == "__main__":
    main()
