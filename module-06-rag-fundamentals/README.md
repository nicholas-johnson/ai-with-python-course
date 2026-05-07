# Module 6 — RAG Fundamentals

**Ground truth from the archive.** Retrieval-Augmented Generation lets the DSS Pathfinder answer from ship logs, mission briefs, and star charts — not from guesses. This module covers chunking, embeddings, vector stores, retrieval strategies, grounded prompting with citations, and how to evaluate RAG quality.

## Learning goals

- Design **chunking** strategies (size, overlap, structure-aware splits) for long-form ship logs and manuals.
- Produce **embeddings**, store them in a **vector index** (local first, then managed options), and query effectively.
- Apply **retrieval strategies**: hybrid search, metadata filters, reranking, and prompt patterns for **grounded answers with citations**.
- Run basic **RAG evaluation**: recall/precision on retrieval, and **adversarial** or ambiguous queries.

## Topics

- Chunking text for retrieval (windows, overlap, boundaries).
- Embeddings and vector stores (local / file-backed first; optional cloud vector DB).
- Retrieval: dense vs sparse, hybrid search, filters, rerankers.
- Prompting for grounded responses and **citation linking** to source chunks.
- RAG evaluation metrics, failure modes, and adversarial test queries.

## Demos

```bash
python module-06-rag-fundamentals/demo/01_chunking.py
python module-06-rag-fundamentals/demo/02_embeddings_vectors.py
python module-06-rag-fundamentals/demo/03_retrieval_strategies.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-document-chunker`](exercises/01-document-chunker/) | Chunk **ship logs** into overlapping windows for indexing. |
| [`exercises/02-vector-search`](exercises/02-vector-search/) | **Embed** and **search** the mission archives. |
| [`exercises/03-rag-pipeline`](exercises/03-rag-pipeline/) | End-to-end RAG with **citation linking** back to sources. |

Run tests for this module:

```bash
pytest module-06-rag-fundamentals/
```

## Slides

From repo root: `pnpm slides:06`, or `cd module-06-rag-fundamentals/slides && pnpm dev`.

## Reference

- [LangChain — RAG overview](https://python.langchain.com/docs/tutorials/rag/)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss/wiki)
- [OpenAI — Embeddings guide](https://platform.openai.com/docs/guides/embeddings)
