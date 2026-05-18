"""
Exercise 03 — RAG Chain (solution)
Run:  python solution.py
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
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CREW = json.loads((PROJECT_ROOT / "data" / "crew.json").read_text())

SENSOR_DATA = {
    "hull_temperature": {"value": 272, "unit": "K", "status": "nominal"},
    "reactor_output": {"value": 94.2, "unit": "%", "status": "nominal"},
    "shield_integrity": {"value": 87, "unit": "%", "status": "warning"},
    "oxygen_level": {"value": 21.1, "unit": "%", "status": "nominal"},
    "radiation": {"value": 0.3, "unit": "mSv/h", "status": "nominal"},
}

# --- Classifier chain from Exercise 01 ---

_classify_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
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


# --- Tools from Exercise 02 ---

@tool
def classify(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    return json.dumps(classify_report(report))


@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor. Available: hull_temperature, reactor_output, shield_integrity, oxygen_level, radiation."""
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
     "You are the DSS Pathfinder AI assistant. "
     "Use your tools to help the crew. Do not guess — always use a tool when data is needed."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(ChatOpenAI(model=MODEL, temperature=0), tools, agent_prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_agent(query: str) -> str:
    return executor.invoke({"input": query})["output"]


# --- RAG chain (Exercise 03) ---

def load_documents() -> tuple[list[str], list[dict]]:
    """Load ship logs and return (texts, metadatas)."""
    logs = json.loads((PROJECT_ROOT / "data" / "ship_logs.json").read_text())
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
    """Create the LCEL RAG chain. Returns (chain, retriever)."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    rag_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are the DSS Pathfinder knowledge assistant.\n"
            "Answer using ONLY the sources below. Cite sources as [Source N].\n"
            "If the sources don't contain the answer, say so.",
        ),
        ("human", "Sources:\n{context}\n\nQuestion: {question}"),
    ])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | ChatOpenAI(model=MODEL, temperature=0)
        | StrOutputParser()
    )
    return chain, retriever


def ask(chain, retriever, question: str) -> tuple[str, list]:
    """Run a RAG query. Returns (answer, retrieved_docs)."""
    docs = retriever.invoke(question)
    answer = chain.invoke(question)
    return answer, docs


def ask_norag(question: str) -> str:
    """Answer without RAG for comparison."""
    model = ChatOpenAI(model=MODEL, temperature=0)
    return model.invoke([{"role": "user", "content": question}]).content


def main():
    print("Building index...")
    texts, metadatas = load_documents()
    vectorstore = build_vectorstore(texts, metadatas)
    chain, retriever = build_rag_chain(vectorstore)
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
