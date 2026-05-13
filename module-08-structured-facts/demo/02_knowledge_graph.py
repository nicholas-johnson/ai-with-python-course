"""Demo 02 — Building a knowledge graph from extracted facts.

Demonstrates entity extraction, relationship modelling, and graph
queries using an in-memory graph (NetworkX-style dict-of-dicts).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    name: str
    entity_type: str
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class Relationship:
    source: str
    target: str
    relation: str
    metadata: dict[str, str] = field(default_factory=dict)


class KnowledgeGraph:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.edges: list[Relationship] = []

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.name] = entity

    def add_relationship(self, rel: Relationship) -> None:
        self.edges.append(rel)

    def neighbours(self, name: str) -> list[Relationship]:
        return [e for e in self.edges if e.source == name or e.target == name]

    def find_path(self, start: str, end: str, max_depth: int = 4) -> list[str] | None:
        visited: set[str] = set()
        queue: list[list[str]] = [[start]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == end:
                return path
            if node in visited or len(path) > max_depth:
                continue
            visited.add(node)
            for rel in self.neighbours(node):
                next_node = rel.target if rel.source == node else rel.source
                queue.append([*path, next_node])
        return None


def main() -> None:
    print("=== Knowledge Graph Demo ===\n")

    graph = KnowledgeGraph()

    graph.add_entity(Entity("Vasquez", "crew", {"role": "Chief Engineer"}))
    graph.add_entity(Entity("Chen", "crew", {"role": "Navigation Officer"}))
    graph.add_entity(Entity("Okafor", "crew", {"role": "Doctor"}))
    graph.add_entity(Entity("port thruster array", "system"))
    graph.add_entity(Entity("Kepler-442 debris field", "hazard"))
    graph.add_entity(Entity("cargo bay 2", "location"))

    graph.add_relationship(Relationship("Vasquez", "port thruster array", "repaired"))
    graph.add_relationship(Relationship("Chen", "Kepler-442 debris field", "plotted_avoidance"))
    graph.add_relationship(Relationship("Okafor", "cargo bay 2", "reported_radiation"))

    print(f"Entities: {len(graph.entities)}")
    print(f"Relationships: {len(graph.edges)}\n")

    for name in ["Vasquez", "Okafor"]:
        rels = graph.neighbours(name)
        print(f"{name} connections:")
        for r in rels:
            print(f"  --[{r.relation}]--> {r.target}")
    print()

    path = graph.find_path("Vasquez", "cargo bay 2")
    print(f"Path Vasquez -> cargo bay 2: {' -> '.join(path) if path else 'not found'}")


if __name__ == "__main__":
    main()
