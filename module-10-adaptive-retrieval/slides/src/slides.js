export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 10 — Adaptive Retrieval',
      subtitle: 'Retrieve intelligently, not blindly',
      icon: 'search',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Static RAG is not enough',
      points: [
        'A fixed pipeline stuffs context and hopes for the best.',
        'Adaptive retrieval reasons about what to look up, where, and whether the results are good enough.',
        'Routing, decomposition, self-critique, and multi-source orchestration.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build a **retrieval router** that selects the right backend per query.',
        'Implement **query decomposition** for complex multi-part questions.',
        'Add a **self-critique loop** (corrective RAG) that re-retrieves when quality is low.',
        'Orchestrate **multi-source retrieval** with merge and relevance scoring.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Retrieval routing',
      icon: 'git-branch',
      points: [
        'Not all queries should go to the vector store.',
        '**Relationship queries** → knowledge graph ("Who reports to Voss?").',
        '**Exact-match queries** → keyword search ("Error code FTL-4092").',
        '**Semantic queries** → vector search ("Tell me about hull repairs").',
        'Classify first, then dispatch to the right backend.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Retrieval router',
      code: `class RetrievalBackend(Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    KEYWORD = "keyword"

@dataclass
class RoutingDecision:
    backend: RetrievalBackend
    confidence: float
    reasoning: str

def classify_query(query: str) -> RoutingDecision:
    q = query.lower()
    if any(kw in q for kw in ["relationship", "connected", "who"]):
        return RoutingDecision(
            RetrievalBackend.GRAPH, 0.85,
            "Relationship query → graph")
    if any(kw in q for kw in ["error code", "serial", "exact"]):
        return RoutingDecision(
            RetrievalBackend.KEYWORD, 0.85,
            "Exact-match query → keyword")
    return RoutingDecision(
        RetrievalBackend.VECTOR, 0.70,
        "Default → semantic search")`,
      highlights: [
        'Heuristic rules are a good starting point; upgrade to LLM classification later',
        'Confidence and reasoning make routing decisions debuggable',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Query decomposition',
      icon: 'divide',
      points: [
        'Complex questions often contain **multiple sub-questions**.',
        '"Compare hull integrity on decks 5 and 7" → two lookups.',
        'Decompose → retrieve for each sub-query → merge answers.',
        'The LLM can do the decomposition: "Break this into focused sub-queries."',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Decompose and retrieve',
      code: `def decompose(question: str, llm) -> list[str]:
    prompt = (
        "Break this question into independent "
        "sub-queries (one per line):\\n"
        f"{question}"
    )
    response = llm.chat(prompt)
    return [q.strip() for q in response.split("\\n") if q.strip()]

def retrieve_decomposed(question, llm, retrieve_fn):
    sub_queries = decompose(question, llm)
    all_results = []
    for sq in sub_queries:
        all_results.extend(retrieve_fn(sq))
    return deduplicate(all_results)`,
      highlights: [
        'Each sub-query gets its own retrieval pass',
        'Deduplication prevents the same chunk from appearing multiple times',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Self-critique (corrective RAG)',
      icon: 'refresh-cw',
      points: [
        'After retrieval, **evaluate** whether the results are relevant.',
        'If quality is low: **refine the query** and try again.',
        'If quality is acceptable: proceed to generation.',
        'Max attempts prevent infinite loops on unanswerable questions.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Self-critique loop',
      code: `def retrieval_with_critique(query, retrieve_fn,
                             critique_fn, max_attempts=3):
    for attempt in range(max_attempts):
        results = retrieve_fn(query)
        quality = critique_fn(query, results)

        if quality.score >= 0.7:
            return results

        query = refine_query(query, quality.feedback)

    return results  # best effort after max attempts

def critique_fn(query, results):
    relevant = [r for r in results if r["score"] > 0.5]
    score = len(relevant) / max(len(results), 1)
    feedback = ("Too few relevant results"
                if score < 0.7 else "OK")
    return Quality(score=score, feedback=feedback)`,
      highlights: [
        'The critique function evaluates retrieval, not generation',
        'Query refinement uses the critique feedback as a hint',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Multi-source orchestration',
      icon: 'layers',
      points: [
        '**Fan-out**: send the query to multiple backends in parallel.',
        '**Merge**: combine result lists, deduplicate by source_id.',
        '**Rank**: score each result by relevance and source trust.',
        '**Generate**: feed the top-k merged results to the LLM.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Fan-out, merge, rank',
      code: `async def multi_source_retrieve(query, backends):
    tasks = [backend.search(query) for backend in backends]
    all_results = await asyncio.gather(*tasks)

    merged = {}
    for result_list in all_results:
        for r in result_list:
            key = r["source_id"]
            if key not in merged or r["score"] > merged[key]["score"]:
                merged[key] = r

    ranked = sorted(merged.values(),
                    key=lambda r: r["score"], reverse=True)
    return ranked[:10]`,
      highlights: [
        'Parallel fan-out minimises total latency',
        'Dedup by source_id keeps the highest-scoring version of each result',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Static vs adaptive RAG',
      left: {
        label: 'Static RAG',
        items: [
          'One retrieval backend',
          'Fixed query → fixed results',
          'No quality check on retrieval',
          'Simple and predictable',
        ],
      },
      right: {
        label: 'Adaptive RAG',
        items: [
          'Routes to the best backend',
          'Decomposes complex questions',
          'Self-critique refines poor results',
          'Higher quality, more moving parts',
        ],
      },
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 10',
      rules: [
        {
          rule: 'Route before you retrieve',
          example: 'Wrong backend = irrelevant results no matter the query.',
          icon: 'git-branch',
        },
        {
          rule: 'Critique the retrieval, not just the answer',
          example: 'Bad input to the LLM guarantees a bad output.',
          icon: 'search',
        },
        {
          rule: 'Cap your critique loops',
          example: 'max_attempts prevents infinite re-retrieval on impossible questions.',
          icon: 'shield',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Intelligent retrieval',
      points: [
        '01 — Retrieval router: classify and dispatch to vector, graph, or keyword',
        '02 — Self-critique: evaluate results and refine queries when quality is low',
        '03 — Multi-source QA: fan out, merge, rank, and answer with citations',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Retrieval upgraded — Module 10',
      subtitle: 'Smart retrieval, adaptive loops. Next: ship it to production.',
      icon: 'party-popper',
    },
  },
];
