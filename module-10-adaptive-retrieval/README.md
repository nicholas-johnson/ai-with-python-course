# Module 10 — Adaptive Retrieval

**Don't retrieve blindly — retrieve intelligently.** A static RAG pipeline stuffs context and hopes for the best. An adaptive retrieval agent reasons about *what* to look up, *where* to look, and *whether the results are good enough* before answering. This module teaches query decomposition, retrieval routing, self-critique loops, and multi-source orchestration on the DSS Pathfinder.

## Learning goals

- Build a **retrieval router** that selects the right source (vector store, knowledge graph, API, keyword search) based on query type.
- Implement **query decomposition** — breaking complex questions into focused sub-queries.
- Add a **self-critique loop** (corrective RAG) that evaluates retrieved documents and re-retrieves when quality is low.
- Orchestrate **multi-source retrieval** — merging results from different backends with relevance scoring.

## Instructor notes

- **Retrieval routing** (`demo/01_retrieval_routing.py`): classifying queries and dispatching to the right backend — vector vs graph vs keyword.
- **Self-critique** (`demo/02_self_critique.py`): evaluating retrieval quality, deciding to refine the query, re-retrieve, or answer with caveats.
- **Multi-source orchestration** (`demo/03_multi_source.py`): fan-out to multiple sources, merge, deduplicate, and rank.

## Demos

```bash
python module-10-adaptive-retrieval/demo/01_retrieval_routing.py
python module-10-adaptive-retrieval/demo/02_self_critique.py
python module-10-adaptive-retrieval/demo/03_multi_source.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-retrieval-router`](exercises/01-retrieval-router/) | Route queries to vector search, graph lookup, or keyword search based on intent classification. |
| [`exercises/02-self-critique`](exercises/02-self-critique/) | Evaluate retrieval quality and re-query with refined terms when results are poor. |
| [`exercises/03-multi-source-qa`](exercises/03-multi-source-qa/) | Fan out to multiple retrieval backends, merge results, and answer with ranked citations. |

Run tests for this module:

```bash
pytest module-10-adaptive-retrieval/
```

## Slides

From repo root: `pnpm slides:10`, or `cd module-10-adaptive-retrieval/slides && pnpm dev`.

## Reference

- [Self-RAG paper (arXiv)](https://arxiv.org/abs/2310.11511)
- [Corrective RAG paper (arXiv)](https://arxiv.org/abs/2401.15884)
- [LangGraph — adaptive RAG tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/)
- [LlamaIndex — query routing](https://docs.llamaindex.ai/en/stable/)
