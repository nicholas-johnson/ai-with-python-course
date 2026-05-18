"""
Exercise 03 — RAG Chain (CSS Horizon)
Build a LangChain RAG chain over the Horizon knowledge base.

Run:  python start.py
Test: pytest test_start.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_chroma import Chroma
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

MODEL = "gpt-4o-mini"
EXERCISE_DATA = Path(__file__).resolve().parents[1] / "data"
CREW = json.loads((EXERCISE_DATA / "horizon_crew.json").read_text())

SENSOR_DATA = {
    "cargo_hold_pressure": {"value": 101.2, "unit": "kPa", "status": "nominal"},
    "main_drive_output": {"value": 96.0, "unit": "%", "status": "nominal"},
    "docking_seal_integrity": {"value": 94.0, "unit": "%", "status": "nominal"},
    "life_support_o2": {"value": 20.9, "unit": "%", "status": "nominal"},
    "background_radiation": {"value": 0.12, "unit": "mSv/h", "status": "nominal"},
}


# ---------------------------------------------------------------------------
# From Exercise 01 — classifier chain (complete)
# ---------------------------------------------------------------------------

_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the CSS Horizon.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary of the report,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])
_classify_chain = _classify_prompt | ChatOpenAI(model=MODEL, temperature=0) | JsonOutputParser()


def classify_report(report: str) -> dict:
    return _classify_chain.invoke({"report": report})


# ---------------------------------------------------------------------------
# From Exercise 02 — tool agent (complete)
# ---------------------------------------------------------------------------

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

agent_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are the CSS Horizon AI assistant. "
     "Use your tools to help the crew. Do not guess — always use a tool when data is needed."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(ChatOpenAI(model=MODEL, temperature=0), tools, agent_prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_agent(query: str) -> str:
    return executor.invoke({"input": query})["output"]


# ---------------------------------------------------------------------------
# TODO: RAG chain functions
# ---------------------------------------------------------------------------

def load_documents() -> tuple[list[str], list[dict]]:
    """Load ship logs from exercises/data/horizon_logs.json. Returns (texts, metadatas).

    Each metadata dict should have: source (log id), author, category.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def build_vectorstore(texts: list[str], metadatas: list[dict]) -> Chroma:
    """Build a Chroma vectorstore from document texts and metadata."""
    # TODO: implement using Chroma.from_texts with OpenAIEmbeddings
    raise NotImplementedError("TODO")


def format_docs(docs) -> str:
    """Format retrieved documents for the RAG prompt context."""
    # TODO: implement — format as "[Source N: id] content"
    raise NotImplementedError("TODO")


def build_rag_chain(vectorstore: Chroma):
    """Create the LCEL RAG chain. Returns (chain, retriever).

    Steps:
        1. Create a retriever from vectorstore (k=5)
        2. Build a ChatPromptTemplate for RAG (cite sources)
        3. Compose the LCEL chain: retriever | format | prompt | llm | parser
        4. Return (chain, retriever)
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def ask(chain, retriever, question: str) -> tuple[str, list]:
    """Run a RAG query. Returns (answer, retrieved_docs)."""
    # TODO: implement
    raise NotImplementedError("TODO")


def ask_norag(question: str) -> str:
    """Answer without RAG for comparison."""
    # TODO: implement
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

def main():
    print("Building index...")
    texts, metadatas = load_documents()
    vectorstore = build_vectorstore(texts, metadatas)
    chain, retriever = build_rag_chain(vectorstore)
    print(f"Indexed {len(texts)} log entries.\n")

    print("=" * 60)
    print("  EXERCISE 03 — RAG CHAIN")
    print("  Answer questions from the ship's knowledge base")
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
            print(f"\nAgent> {run_agent(last_question)}\n")
            continue

        last_question = user_input
        try:
            answer, last_docs = ask(chain, retriever, user_input)
            print(f"\nRAG> {answer}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


if __name__ == "__main__":
    main()
