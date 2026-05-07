# Module 9 — Structured Facts

**Raw text is unreliable. Structured data is actionable.** The Pathfinder's AI systems need to extract verifiable facts from unstructured ship logs, crew reports, and sensor data — then organise them into a queryable knowledge graph. This module covers structured output generation, fact extraction pipelines, knowledge graph construction, and grounded question-answering that cites its sources.

## Learning goals

- Use **structured outputs** (Pydantic models, JSON Schema) to get reliable, typed data from an LLM.
- Build a **fact extraction pipeline** that decomposes text into individual claims with provenance.
- Construct a **knowledge graph** from extracted entities and relationships.
- Implement **grounded QA** that answers questions from the graph and cites source documents.

## Instructor notes

- **Structured extraction** (`demo/01_structured_extraction.py`): Pydantic models as output schemas, the `instructor` pattern, handling validation failures and retries.
- **Knowledge graph** (`demo/02_knowledge_graph.py`): entity and relationship extraction, building an in-memory graph, querying with traversals.
- **Grounded QA** (`demo/03_grounded_qa.py`): combining graph lookups with RAG retrieval, citation linking, confidence scoring.

## Demos

```bash
python module-09-structured-facts/demo/01_structured_extraction.py
python module-09-structured-facts/demo/02_knowledge_graph.py
python module-09-structured-facts/demo/03_grounded_qa.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-fact-extractor`](exercises/01-fact-extractor/) | Extract structured crew and mission facts from ship logs using Pydantic output schemas. |
| [`exercises/02-knowledge-graph`](exercises/02-knowledge-graph/) | Build a knowledge graph from extracted entities and query it for relationships. |
| [`exercises/03-grounded-qa`](exercises/03-grounded-qa/) | Answer questions from the graph with source citations and confidence scores. |

Run tests for this module:

```bash
pytest module-09-structured-facts/
```

## Slides

From repo root: `pnpm slides:09`, or `cd module-09-structured-facts/slides && pnpm dev`.

## Reference

- [OpenAI — Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Instructor — structured LLM outputs](https://python.useinstructor.com/)
- [Pydantic docs](https://docs.pydantic.dev/latest/)
- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)
- [NetworkX — graph library](https://networkx.org/documentation/stable/)
