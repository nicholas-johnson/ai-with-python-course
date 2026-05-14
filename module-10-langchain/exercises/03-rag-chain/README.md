# Exercise 03 — RAG Chain

**Mission briefing:** Assemble a LangChain **RetrievalQA chain** that answers crew questions by retrieving context from the Pathfinder knowledge base (the vector store you built in module 06).

## Objectives

1. Load or mock a vector store retriever compatible with LangChain.
2. Build a `RetrievalQA` chain (or LCEL equivalent) with a custom prompt.
3. Invoke the chain and verify the answer includes retrieved context.

## Run the tests

```bash
pytest module-10-langchain/exercises/03-rag-chain/test_start.py -v
```
