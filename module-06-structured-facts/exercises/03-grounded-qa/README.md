# Exercise 3: Grounded QA

## Recap

In Exercise 1 you extracted structured facts. In Exercise 2 you built a knowledge graph. Now you'll use both to answer questions with **citations**.

The flow:

```
Question → Extract entities → Traverse graph → Build grounded prompt → Generate cited answer
```

Unlike RAG (which matches by embedding similarity), graph-grounded QA follows **relationships**. "What caused the Meridian to go silent?" traverses edges from the Meridian through containment breach, crew exposure, and emergency jump rather than hoping for a text match. This is complementary to vector search -- graphs are better for relational questions, vectors are better for semantic similarity.

The grounded prompt includes the evidence as numbered facts:

```
[Fact 1] Specimen Theta --caused--> containment breach (confidence: 0.95)
[Fact 2] containment breach --exposed--> Dr. Oshiro (confidence: 0.92)

Question: What caused the crew to evacuate?
```

## What you build

A console Q&A agent in **`start.py`** that answers questions grounded in knowledge graph evidence, with citations.

The Exercise 1 and 2 solutions are provided as `fact_extractor.py` and `graph_builder.py`.

**Key functions:**

| Function | Description |
|---|---|
| `extract_query_entities(question, client)` | Use OpenAI to identify entity names in the question |
| `retrieve_evidence(graph, entities, max_hops)` | Traverse the graph to collect relevant facts |
| `build_grounded_prompt(question, evidence)` | Build a system + user message with `[Fact N]` labels |
| `grounded_qa(question, graph, client)` | End-to-end: extract entities, retrieve, prompt, generate |

## Step-by-step

### 1. Import the provided solutions

```python
from fact_extractor import load_logs, extract_facts, validate_facts
from graph_builder import build_graph, KnowledgeGraph
```

### 2. Implement `extract_query_entities`

Use OpenAI to identify which entities from the question might exist in the graph:

```python
def extract_query_entities(question: str, client, graph: KnowledgeGraph) -> list[str]:
    # Option 1: keyword match against graph nodes
    # Option 2: ask the LLM to identify entities, then fuzzy-match to graph nodes
```

### 3. Implement `retrieve_evidence`

For each identified entity, call `graph.find_connections(entity, max_hops)` and collect the edges. Format each as a dict with `source`, `target`, `relation`, `confidence`.

### 4. Implement `build_grounded_prompt`

Build messages with numbered `[Fact N]` citations, instructing the model to answer using only the provided facts.

### 5. Implement `grounded_qa`

Tie it all together: extract entities, retrieve evidence, build prompt, call OpenAI, return a `GroundedAnswer` dataclass.

### 6. Build the interactive loop

| Command | Action |
|---|---|
| any question | Grounded QA with citations |
| `/evidence` | Show the full evidence from the last query |
| `/nograph` | Re-ask the last question without graph evidence |
| `/hops <n>` | Change traversal depth (default 2) |
| `quit` | Exit |

## Try it

```bash
cd module-06-structured-facts/exercises/03-grounded-qa
python start.py
```

Try asking about the Meridian's crew, what happened to Specimen Theta, or why the distress beacon failed. Use `/nograph` to see how the answer quality drops without evidence.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `retrieve_evidence` returns facts for known entities
- `build_grounded_prompt` includes `[Fact N]` labels
- `grounded_qa` returns a `GroundedAnswer` with citations

## Stretch goals

- Add confidence scoring based on how relevant the evidence is
- Implement a follow-up mode that uses previous answers as context
- Combine graph retrieval with vector search for hybrid grounded QA
