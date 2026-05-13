# Exercise 02 — Knowledge Graph

## Mission

Turn extracted facts into a queryable knowledge graph. The Pathfinder needs to answer relational questions like "Who has interacted with cargo bay 2?" and "What is the path between Vasquez and the radiation alert?"

## Objectives

1. Define `Entity` and `Relationship` dataclasses.
2. Implement a `KnowledgeGraph` class with `add_entity`, `add_relationship`, `get_entity`, and `neighbours` methods.
3. Implement `build_graph(facts: list[dict]) -> KnowledgeGraph` that populates a graph from a list of extracted fact dicts.
4. Implement `find_connections(graph, entity_name, max_depth) -> list[Relationship]` that returns all relationships within N hops.

## Run

```bash
pytest module-08-structured-facts/exercises/02-knowledge-graph/test_start.py -v
```
