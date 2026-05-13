# Module 9 — Adaptive Retrieval

> A single retrieval strategy is not enough for a ship with decades of heterogeneous data. Some questions need vector search ("what incidents were similar to this one?"), others need graph traversal ("what caused the cascade failure?"), and others need keyword lookup ("show me log entry CRW-003-2287"). This module builds an adaptive retrieval layer that routes queries to the right backend, decomposes complex questions, critiques its own results, and orchestrates multiple sources into a single grounded answer.

## Learning goals

- **Route queries** to the appropriate retrieval backend (vector, graph, keyword).
- **Decompose** complex queries into simpler sub-queries.
- Build **self-critique loops** (corrective RAG) that refine poor results.
- **Orchestrate multiple sources**: fan-out, merge, and rank.

---

## Retrieval routing

Not all queries are alike. "What happened to the reactor last month?" is a broad semantic question — vector search excels. "What is connected to entity CRW-003?" is a relationship question — graph traversal is the answer. "Show me log ID LOG-2287-0042" is an exact-match lookup — keyword/ID search is fastest.

A retrieval router classifies the query and directs it to the right backend:

```python
from enum import Enum

class RetrievalBackend(Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    KEYWORD = "keyword"

def classify_query(query: str) -> RetrievalBackend:
    q = query.lower()
    relationship_terms = ["connected", "related", "caused", "affected", "between"]
    exact_terms = ["id", "log entry", "code", "exact", "crw-", "msn-"]

    if any(term in q for term in relationship_terms):
        return RetrievalBackend.GRAPH
    if any(term in q for term in exact_terms):
        return RetrievalBackend.KEYWORD
    return RetrievalBackend.VECTOR
```

The routing decision can be heuristic (keyword matching, as above), LLM-based (ask the model which backend is best), or hybrid. Start with heuristics — they are fast, free, and debuggable. Upgrade to LLM routing only if heuristics fail on your query distribution.

---

## Query decomposition

Complex questions often need information from multiple sources. "Compare reactor performance before and after the ion storm" requires two retrievals: pre-storm data and post-storm data. Decomposition splits the query into sub-queries that can each be routed and retrieved independently.

```python
def decompose_query(query: str) -> list[str]:
    """Split a complex query into simpler sub-queries."""
    prompt = f"""Break this question into 2-4 simpler sub-questions that can
each be answered independently. Return as a JSON list of strings.

Question: {query}"""
    response = llm.complete(prompt)
    return json.loads(response)
```

Each sub-query goes through the routing and retrieval pipeline. Results are collected and merged before the final answer generation.

---

## Self-critique — corrective RAG

What if the retrieved results are irrelevant? Standard RAG would pass bad evidence to the model and get a hallucinated answer. **Corrective RAG** adds a critique step: evaluate the results, and if they are poor, refine the query and try again.

```python
def critique_results(query: str, results: list[dict]) -> CritiqueResult:
    """Evaluate whether the results are relevant to the query."""
    if not results:
        return CritiqueResult(quality="poor", reason="No results found")

    relevance_scores = [score_relevance(query, r["text"]) for r in results]
    avg_score = sum(relevance_scores) / len(relevance_scores)

    if avg_score > 0.7:
        return CritiqueResult(quality="good", score=avg_score)
    return CritiqueResult(quality="poor", score=avg_score, reason="Low relevance")

def retrieval_loop(query: str, max_attempts: int = 3) -> list[dict]:
    for attempt in range(max_attempts):
        results = retrieve(query)
        critique = critique_results(query, results)

        if critique.quality == "good":
            return results

        query = refine_query(query, critique.reason)

    return results  # best effort after max attempts
```

The loop refines the query based on what went wrong — "no results" triggers a broader search, "low relevance" triggers rephrasing. Cap the attempts to prevent infinite loops and wasted tokens.

---

## Multi-source orchestration

Production systems have multiple data sources: a vector store for documents, a knowledge graph for relationships, a keyword index for exact matches, and possibly external APIs. Multi-source orchestration queries them in parallel, merges the results, and ranks the combined set.

**Fan-out** — send the query (or sub-queries) to all relevant backends concurrently:

```python
async def fan_out(query: str, backends: list[Backend]) -> list[list[dict]]:
    tasks = [backend.search(query) for backend in backends]
    return await asyncio.gather(*tasks)
```

**Merge and rank** — combine results from all sources, deduplicate by source ID, and rank by relevance score:

```python
def merge_and_rank(result_sets: list[list[dict]]) -> list[dict]:
    seen = set()
    merged = []
    for results in result_sets:
        for r in results:
            if r["source_id"] not in seen:
                seen.add(r["source_id"])
                merged.append(r)
    return sorted(merged, key=lambda r: r["score"], reverse=True)
```

The merged, ranked results feed into the grounded prompt builder from Module 5. The answer cites sources from multiple backends — the crew sees evidence from logs, graphs, and documents in a single response.

---

## Field rules

- **Route before you retrieve.** The wrong backend wastes time and returns noise.
- **Critique before you generate.** Bad evidence in → hallucinated answer out.
- **Cap self-critique loops.** Three attempts is usually enough; more wastes tokens.
- **Fan out in parallel.** `asyncio.gather` over sequential searches saves latency.

---

## Demos

```bash
python module-09-adaptive-retrieval/demo/01_retrieval_routing.py
python module-09-adaptive-retrieval/demo/02_self_critique.py
python module-09-adaptive-retrieval/demo/03_multi_source.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-retrieval-router`](exercises/01-retrieval-router/) | Classify queries and route to vector, graph, or keyword backends. |
| [`exercises/02-self-critique`](exercises/02-self-critique/) | Critique retrieval results and refine queries in a loop. |
| [`exercises/03-multi-source-qa`](exercises/03-multi-source-qa/) | Fan-out to multiple backends, merge, rank, and answer with citations. |

Run tests for this module:

```bash
pytest module-09-adaptive-retrieval/
```

## Slides

From repo root: `pnpm slides:09`, or `cd module-09-adaptive-retrieval/slides && pnpm dev`.

## Reference

- [Corrective RAG (Yan et al. 2024)](https://arxiv.org/abs/2401.15884)
- [Adaptive RAG (Jeong et al. 2024)](https://arxiv.org/abs/2403.14403)
- [Self-RAG (Asai et al. 2023)](https://arxiv.org/abs/2310.11511)
