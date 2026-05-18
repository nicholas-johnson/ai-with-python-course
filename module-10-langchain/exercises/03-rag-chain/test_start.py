"""Tests for Exercise 03 — RAG Chain."""

import pytest

from start import ask, load_documents, build_vectorstore, build_rag_chain


@pytest.mark.skip(reason="Skeleton — implement RAG chain functions")
def test_ask_returns_answer_and_docs():
    texts, metadatas = load_documents()
    vectorstore = build_vectorstore(texts, metadatas)
    chain, retriever = build_rag_chain(vectorstore)

    answer, docs = ask(chain, retriever, "What happened with docking seal ring 3 at L5-Prime?")
    assert isinstance(answer, str)
    assert len(answer) > 0
    assert isinstance(docs, list)
