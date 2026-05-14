"""
Graph builder -- provided from Exercise 2 solution.
Import this to get KnowledgeGraph and build_graph.
"""

import networkx as nx
from fact_extractor import Fact


class KnowledgeGraph:
    """Knowledge graph wrapping a networkx DiGraph."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_fact(self, fact: Fact):
        """Add a fact as nodes + edge in the graph."""
        self.graph.add_node(fact.subject)
        self.graph.add_node(fact.object)
        self.graph.add_edge(
            fact.subject,
            fact.object,
            relation=fact.predicate,
            confidence=fact.confidence,
            source_text=fact.source_text,
        )

    def neighbours(self, entity: str) -> list[tuple]:
        """Return all edges connected to the entity (incoming + outgoing)."""
        edges = []
        if entity in self.graph:
            for _, target, data in self.graph.out_edges(entity, data=True):
                edges.append((entity, target, data.get("relation", "?"), data.get("confidence", 0)))
            for source, _, data in self.graph.in_edges(entity, data=True):
                edges.append((source, entity, data.get("relation", "?"), data.get("confidence", 0)))
        return edges

    def find_path(self, start: str, end: str) -> list[str] | None:
        """Find shortest path between two entities."""
        try:
            return nx.shortest_path(self.graph, start, end)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_connections(self, entity: str, max_hops: int = 2) -> list[tuple]:
        """BFS from entity, return all edges within max_hops."""
        if entity not in self.graph:
            return []

        visited = set()
        queue = [(entity, 0)]
        edges = []

        while queue:
            node, depth = queue.pop(0)
            if node in visited or depth > max_hops:
                continue
            visited.add(node)

            for _, target, data in self.graph.out_edges(node, data=True):
                edges.append((node, target, data.get("relation", "?"), data.get("confidence", 0)))
                if target not in visited and depth + 1 <= max_hops:
                    queue.append((target, depth + 1))
            for source, _, data in self.graph.in_edges(node, data=True):
                edges.append((source, node, data.get("relation", "?"), data.get("confidence", 0)))
                if source not in visited and depth + 1 <= max_hops:
                    queue.append((source, depth + 1))

        return edges


def build_graph(facts: list[Fact]) -> KnowledgeGraph:
    """Build a knowledge graph from a list of Facts."""
    kg = KnowledgeGraph()
    for fact in facts:
        kg.add_fact(fact)
    return kg
