# Exercise 2: Knowledge Graph

## Recap

A **knowledge graph** represents information as entities (nodes) and relationships (edges). Unlike a flat list of facts, a graph lets you traverse connections:

- "Who was exposed to Specimen Theta?" -- follow edges from "Specimen Theta" to find crew members
- "What did Engineer Marquez assess?" -- follow edges from "Juno Marquez" to find systems
- "What connects the containment breach to the emergency jump?" -- find a path through the graph

**networkx** is Python's standard graph library:

```python
import networkx as nx

G = nx.DiGraph()
G.add_node("Juno Marquez", type="crew")
G.add_edge("Juno Marquez", "Meridian reactor", relation="assessed", confidence=0.95)

# Find neighbours
list(G.successors("Juno Marquez"))  # ["Meridian reactor"]

# Find shortest path
nx.shortest_path(G, "Specimen Theta", "emergency jump")
```

In this exercise you'll turn the facts from Exercise 1 into a traversable graph.

## What you build

A console app in **`start.py`** that extracts facts from all salvage mission logs, builds a networkx knowledge graph, and lets you explore it interactively.

The Exercise 1 solution is provided as `fact_extractor.py`.

**Key types/functions:**

| Function | Description |
|---|---|
| `KnowledgeGraph` | Wrapper around `nx.DiGraph` with `add_fact`, `neighbours`, `find_path`, `find_connections` |
| `build_graph(facts)` | Populate a graph from a list of `Fact` objects |

## Step-by-step

### 1. Import the fact extractor

The Exercise 1 solution is provided as `fact_extractor.py`:

```python
from fact_extractor import load_logs, extract_facts, validate_facts, Fact
```

### 2. Implement `KnowledgeGraph`

Wrap `nx.DiGraph` with helper methods:

- `add_fact(fact)` -- add subject and object as nodes, predicate as an edge
- `neighbours(entity)` -- return all edges connected to an entity
- `find_path(start, end)` -- shortest path between two entities
- `find_connections(entity, max_hops)` -- BFS to find everything within N hops

### 3. Implement `build_graph`

Loop over all facts, call `add_fact` for each. Track entity types (infer from predicates or position: subjects are often people/systems, objects are often locations/values).

### 4. Build the interactive loop

| Command | Action |
|---|---|
| any entity name | Show all connections for that entity |
| `/path <from> -> <to>` | Find shortest path between entities |
| `/stats` | Show entity count, edge count, graph density |
| `/entities` | List all entities |
| `/related <entity>` | Find everything within 2 hops |
| `quit` | Exit |

## Try it

```bash
cd module-06-structured-facts/exercises/02-knowledge-graph
python start.py
```

Try querying crew members (Juno Marquez, Dr. Idris Kone), systems (Meridian reactor, containment field), and events (containment breach, emergency jump). Use `/path` to trace the chain of events that led to the Meridian's silence.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `KnowledgeGraph.add_fact` creates nodes and edges
- `neighbours` returns connected relationships
- `find_path` finds shortest paths
- `build_graph` populates from a list of facts

## Stretch goals

- Detect entity types automatically (person, system, location)
- Add edge weights based on confidence
- Implement PageRank to find the most important entities
