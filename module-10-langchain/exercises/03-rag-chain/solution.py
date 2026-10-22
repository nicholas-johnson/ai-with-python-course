"""
Exercise 03 — RAG Chain (solution)
Run:  python solution.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
EXERCISE_DATA = Path(__file__).resolve().parents[1] / "data"
CREW = json.loads((EXERCISE_DATA / "horizon_crew.json").read_text())

SENSOR_DATA = {
    "cargo_hold_pressure": {"value": 101.2, "unit": "kPa", "status": "nominal"},
    "main_drive_output": {"value": 96.0, "unit": "%", "status": "nominal"},
    "docking_seal_integrity": {"value": 94.0, "unit": "%", "status": "nominal"},
    "life_support_o2": {"value": 20.9, "unit": "%", "status": "nominal"},
    "background_radiation": {"value": 0.12, "unit": "mSv/h", "status": "nominal"},
}

# --- Classifier chain from Exercise 01 ---

class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the CSS Horizon.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])
_classify_model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
_classify_chain = _classify_prompt | _classify_model.with_structured_output(Classification)


def classify_report(report: str) -> dict:
    return _classify_chain.invoke({"report": report}).model_dump()


# --- Tools from Exercise 02 ---

@tool
def classify(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    return json.dumps(classify_report(report))


@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor. Available: cargo_hold_pressure, main_drive_output, docking_seal_integrity, life_support_o2, background_radiation."""
    data = SENSOR_DATA.get(sensor_name)
    if not data:
        return json.dumps({"error": f"Unknown sensor '{sensor_name}'", "available": list(SENSOR_DATA.keys())})
    return json.dumps(data)


@tool
def query_crew(department: str) -> str:
    """Look up crew members by department. Departments: command, science, engineering, medical, operations, security."""
    results = [c for c in CREW if c["department"] == department]
    if not results:
        departments = sorted(set(c["department"] for c in CREW))
        return json.dumps({"error": f"No crew in '{department}'", "departments": departments})
    return json.dumps(results)


tools = [classify, read_sensor, query_crew]

SYSTEM_PROMPT = (
    "You are the CSS Horizon AI assistant. "
    "Use your tools to help the crew. Do not guess — always use a tool when data is needed."
)

agent = create_agent(ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0), tools, system_prompt=SYSTEM_PROMPT)


def run_agent(query: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].text


# --- RAG chain (Exercise 03) ---

def load_documents() -> tuple[list[str], list[dict]]:
    """Load ship logs and return (texts, metadatas)."""
    logs = json.loads((EXERCISE_DATA / "horizon_logs.json").read_text())
    texts = [log["content"] for log in logs]
    metadatas = [
        {"source": log["id"], "author": log["author"], "category": log["category"]}
        for log in logs
    ]
    return texts, metadatas


def build_vectorstore(texts: list[str], metadatas: list[dict]) -> Chroma:
    """Build a Chroma vectorstore from document texts and metadata."""
    return Chroma.from_texts(texts, OpenAIEmbeddings(), metadatas=metadatas)


def format_docs(docs) -> str:
    return "\n\n".join(
        f"[Source {i+1}: {doc.metadata.get('source', '?')}] {doc.page_content}"
        for i, doc in enumerate(docs)
    )


def build_rag_chain(vectorstore: Chroma):
    """Create the LCEL RAG chain. Returns (chain, retriever).

    chain.invoke(question) returns {"question", "docs", "answer"} — the answer
    and the documents it was grounded on, from a single retrieval.
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    rag_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are the CSS Horizon knowledge assistant.\n"
            "Answer using ONLY the sources below. Cite sources as [Source N].\n"
            "If the sources don't contain the answer, say so.",
        ),
        ("human", "Sources:\n{context}\n\nQuestion: {question}"),
    ])

    answer_chain = (
        RunnablePassthrough.assign(context=lambda x: format_docs(x["docs"]))
        | rag_prompt
        | ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
        | StrOutputParser()
    )
    chain = (
        {"docs": retriever, "question": RunnablePassthrough()}
        | RunnablePassthrough.assign(answer=answer_chain)
    )
    return chain, retriever


def ask(chain, question: str) -> tuple[str, list]:
    """Run a RAG query. Returns (answer, retrieved_docs)."""
    result = chain.invoke(question)
    return result["answer"], result["docs"]


def build_rag_agent(retriever):
    """Agentic RAG: give the Exercise 02 agent a tool that searches the logs."""

    @tool
    def search_logs(query: str) -> str:
        """Search the CSS Horizon ship logs. Use for questions about past events, surveys, or operations."""
        return format_docs(retriever.invoke(query))

    return create_agent(
        ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0),
        [*tools, search_logs],
        system_prompt=SYSTEM_PROMPT + " Cite log sources as [Source N: id] when you use search_logs.",
    )


def run_rag_agent(agent, question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].text


def ask_norag(question: str) -> str:
    """Answer without RAG for comparison."""
    model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
    return model.invoke([{"role": "user", "content": question}]).text


def main():
    print("Building index...")
    texts, metadatas = load_documents()
    vectorstore = build_vectorstore(texts, metadatas)
    chain, retriever = build_rag_chain(vectorstore)
    rag_agent = build_rag_agent(retriever)
    print(f"Indexed {len(texts)} log entries.\n")

    print("=" * 60)
    print("  EXERCISE 03 — RAG CHAIN")
    print("=" * 60)
    print("\nCommands: /sources, /norag, /agent, quit\n")

    last_question = None
    last_docs: list = []

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
            print(f"\nNo-RAG> {ask_norag(last_question)}\n")
            continue
        if user_input == "/agent" and last_question:
            print(f"\nAgent> {run_rag_agent(rag_agent, last_question)}\n")
            continue

        last_question = user_input
        try:
            answer, last_docs = ask(chain, user_input)
            print(f"\nRAG> {answer}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


if __name__ == "__main__":
    main()
