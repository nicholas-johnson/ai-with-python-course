"""Tests for Exercise 03 — RAG Chain."""

import pytest

from start import ask, load_documents, build_vectorstore, build_rag_chain


@pytest.mark.skip(reason="Skeleton — implement RAG chain functions")
def test_ask_returns_answer_and_docs():
    texts, metadatas = load_documents()
    vectorstore = build_vectorstore(texts, metadatas)
    chain, retriever = build_rag_chain(vectorstore)

    answer, docs = ask(chain, retriever, "What are the navigation protocols for sector 7?")
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert isinstance(docs, list)
