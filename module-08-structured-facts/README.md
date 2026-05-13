# Module 8 — Structured Facts

> The Pathfinder's logs and sensor data are full of facts — but they are buried in free text. "Reactor efficiency dropped to 72% after the ion storm on stardate 2287.3" contains an entity (the reactor), a measurement (72%), a cause (ion storm), and a timestamp. This module teaches the agent to extract structured facts from text, organise them into a knowledge graph, and answer questions grounded in verified evidence.

## Learning goals

- Use **Pydantic models** to define structured output schemas.
- Build a **fact extraction pipeline**: claims, provenance, and confidence scores.
- Construct a **knowledge graph**: entities, relationships, and traversal with `networkx`.
- Implement **grounded QA** from graphs with citations.

---

## Why structure matters

Free-text answers are easy to generate but hard to verify. "The reactor is running at reduced capacity" — is that 90% or 50%? When was it last inspected? Who filed the report? Structured outputs give you discrete fields that code can validate, compare, and aggregate.

The shift from unstructured to structured is the foundation of reliable AI systems. If the model says `{"efficiency": 0.72, "confidence": 0.95}`, your code can check the range, compare to thresholds, and decide whether to alert the crew — all without parsing natural language.

---

## Pydantic models for structured outputs

Pydantic models define the exact shape of the data you want from the LLM. The model validates the response, coerces types, and raises clear errors when the output does not match.

```python
from pydantic import BaseModel, Field

class Fact(BaseModel):
    claim: str = Field(description="A single factual claim")
    subject: str = Field(description="The entity this fact is about")
    confidence: float = Field(ge=0.0, le=1.0, description="Model's confidence")
    source: str = Field(description="Where this fact came from")

class ExtractionResult(BaseModel):
    facts: list[Fact]
    raw_text: str
```

Pass the schema as a JSON Schema string in the system prompt, or use the OpenAI structured output mode that constrains decoding directly. Either way, the model's output parses into a typed Python object you can work with programmatically.

---

## Fact extraction pipeline

Extraction turns free text into structured facts. The pipeline has three stages:

**Extract** — prompt the LLM with text and a schema. Ask it to identify every factual claim, the subject entity, and a confidence score.

```python
def extract_facts(text: str, llm) -> list[Fact]:
    prompt = f"""Extract every factual claim from the following text.
For each fact, return: claim, subject, confidence (0-1), and source.
Return as a JSON array of objects.

Text: {text}"""
    response = llm.complete(prompt)
    return [Fact.model_validate(f) for f in json.loads(response)]
```

**Validate** — filter facts below a confidence threshold (0.7 is a good starting point). Drop duplicates by comparing claim text with fuzzy matching or exact subject+claim pairs.

```python
def validate_facts(facts: list[Fact], threshold: float = 0.7) -> list[Fact]:
    seen = set()
    validated = []
    for fact in facts:
        if fact.confidence < threshold:
            continue
        key = (fact.subject.lower(), fact.claim.lower())
        if key not in seen:
            seen.add(key)
            validated.append(fact)
    return validated
```

**Store** — validated facts go into the knowledge graph (next section) or a structured database for later retrieval.

---

## Knowledge graphs

A knowledge graph represents information as entities (nodes) and relationships (edges). Unlike a flat list of facts, a graph lets you traverse connections: "What systems were affected by the ion storm?" → follow edges from the "ion storm" entity to find "reactor", "navigation array", "comms relay".

```python
import networkx as nx

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_entity(self, entity_id: str, label: str, properties: dict = None):
        self.graph.add_node(entity_id, label=label, **(properties or {}))

    def add_relationship(self, source: str, target: str, relation: str):
        self.graph.add_edge(source, target, relation=relation)

    def find_connections(self, entity_id: str, max_hops: int = 2) -> list[dict]:
        """Find all entities within max_hops of the given entity."""
        paths = nx.single_source_shortest_path(self.graph, entity_id, cutoff=max_hops)
        return [
            {"entity": target, "path": path, "hops": len(path) - 1}
            for target, path in paths.items()
            if target != entity_id
        ]
```

Build the graph from extracted facts: each fact's subject becomes an entity, and relationships are derived from the claims ("reactor → affected_by → ion_storm").

**Traversal** is what makes graphs powerful. A vector search finds similar text; a graph search finds connected entities. Asking "What caused the reactor anomaly?" traverses the `caused_by` edges rather than hoping for a semantic match.

---

## Grounded QA from graphs

With a knowledge graph populated, you can answer questions by:

1. **Retrieving** relevant entities and their connections (within N hops of the query's subject).
2. **Building a grounded prompt** that includes the retrieved facts with provenance.
3. **Generating** an answer that cites specific facts.

```python
def grounded_qa(query: str, graph: KnowledgeGraph, llm) -> GroundedAnswer:
    entities = graph.find_relevant(query)

    if not entities:
        return GroundedAnswer(
            answer="I don't have enough evidence to answer.",
            citations=[],
            confidence=0.2,
        )

    prompt = build_graph_prompt(query, entities)
    response = llm.complete(prompt)
    return parse_grounded_answer(response)
```

When the graph contains no relevant entities, the answer honestly says so with low confidence. This is better than fabricating an answer — the crew can then decide to investigate further.

---

## Field rules

- **Define schemas before extraction.** Pydantic models constrain output to usable structure.
- **Filter by confidence.** Low-confidence facts pollute the graph and mislead downstream QA.
- **Graphs complement vectors.** Use vector search for similarity; use graph traversal for connections.
- **Always cite provenance.** Every fact should trace back to its source document.

---

## Demos

```bash
python module-08-structured-facts/demo/01_structured_extraction.py
python module-08-structured-facts/demo/02_knowledge_graph.py
python module-08-structured-facts/demo/03_grounded_qa.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-fact-extractor`](exercises/01-fact-extractor/) | Extract structured facts from text with confidence and deduplication. |
| [`exercises/02-knowledge-graph`](exercises/02-knowledge-graph/) | Build a knowledge graph from facts and traverse connections. |
| [`exercises/03-grounded-qa`](exercises/03-grounded-qa/) | Answer questions grounded in graph evidence with citations. |

Run tests for this module:

```bash
pytest module-08-structured-facts/
```

## Slides

From repo root: `pnpm slides:08`, or `cd module-08-structured-facts/slides && pnpm dev`.

## Reference

- [Pydantic docs](https://docs.pydantic.dev/)
- [NetworkX](https://networkx.org/)
- [OpenAI — Structured outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Instructor library](https://python.useinstructor.com/)
