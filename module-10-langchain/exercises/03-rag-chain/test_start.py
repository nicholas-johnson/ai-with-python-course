"""Tests for Exercise 03 — RAG Chain."""

import os

import pytest
from start import ask, build_rag_agent, build_rag_chain, build_vectorstore, load_documents

needs_key = pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")


def test_load_documents_returns_texts_and_metadata():
    texts, metadatas = load_documents()
    assert len(texts) == len(metadatas) > 0
    assert {"source", "author", "category"} <= set(metadatas[0])


@pytest.fixture(scope="module")
def rag():
    texts, metadatas = load_documents()
    vectorstore = build_vectorstore(texts, metadatas)
    return build_rag_chain(vectorstore)


@pytest.mark.integration
@needs_key
def test_ask_returns_answer_and_docs(rag):
    chain, _ = rag
    answer, docs = ask(chain, "What happened with docking seal ring 3 at L5-Prime?")
    assert isinstance(answer, str) and answer
    assert isinstance(docs, list) and docs
    assert all(hasattr(d, "page_content") for d in docs)


@pytest.mark.integration
@needs_key
def test_rag_agent_can_search_logs(rag):
    _, retriever = rag
    agent = build_rag_agent(retriever)
    tool_names = {t.name for t in agent.get_graph().nodes["tools"].data.tools_by_name.values()}
    assert "search_logs" in tool_names
