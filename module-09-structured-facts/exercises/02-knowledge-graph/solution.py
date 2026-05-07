"""Exercise 02 — Knowledge Graph (solution)"""

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

    def get_entity(self, name: str) -> Entity | None:
        return self.entities.get(name)

    def neighbours(self, name: str) -> list[Relationship]:
        return [e for e in self.edges if e.source == name or e.target == name]


def build_graph(facts: list[dict]) -> KnowledgeGraph:
    graph = KnowledgeGraph()
    for fact in facts:
        subj, pred, obj = fact["subject"], fact["predicate"], fact["object"]
        if subj not in graph.entities:
            graph.add_entity(Entity(subj, "unknown"))
        if obj not in graph.entities:
            graph.add_entity(Entity(obj, "unknown"))
        graph.add_relationship(Relationship(subj, obj, pred))
    return graph


def find_connections(
    graph: KnowledgeGraph,
    entity_name: str,
    max_depth: int = 2,
) -> list[Relationship]:
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(entity_name, 0)]
    result: list[Relationship] = []

    while queue:
        node, depth = queue.pop(0)
        if node in visited or depth > max_depth:
            continue
        visited.add(node)

        for rel in graph.neighbours(node):
            if rel not in result:
                result.append(rel)
            next_node = rel.target if rel.source == node else rel.source
            if next_node not in visited and depth + 1 <= max_depth:
                queue.append((next_node, depth + 1))

    return result
