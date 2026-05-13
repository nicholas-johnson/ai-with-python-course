"""Exercise 02 — Knowledge Graph

Build a knowledge graph from extracted facts and query it.
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
        """Add an entity to the graph. Overwrites if name already exists."""
        # TODO
        raise NotImplementedError

    def add_relationship(self, rel: Relationship) -> None:
        """Add a directed relationship between two entities."""
        # TODO
        raise NotImplementedError

    def get_entity(self, name: str) -> Entity | None:
        """Return the entity with the given name, or None."""
        # TODO
        raise NotImplementedError

    def neighbours(self, name: str) -> list[Relationship]:
        """Return all relationships where name is source or target."""
        # TODO
        raise NotImplementedError


def build_graph(facts: list[dict]) -> KnowledgeGraph:
    """Populate a KnowledgeGraph from a list of fact dicts.

    Each dict has keys: subject, predicate, object.
    Entities are created from subjects and objects; relationships from predicates.
    """
    # TODO
    raise NotImplementedError


def find_connections(
    graph: KnowledgeGraph,
    entity_name: str,
    max_depth: int = 2,
) -> list[Relationship]:
    """Return all relationships reachable within max_depth hops from entity_name."""
    # TODO: BFS from entity_name, collecting relationships up to max_depth.
    raise NotImplementedError
