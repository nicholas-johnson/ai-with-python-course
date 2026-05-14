"""
Exercise 2 -- Solution
========================
Build a knowledge graph from extracted facts and query it interactively.

Run:  python solution.py
"""

import networkx as nx
from openai import OpenAI

from fact_extractor import Fact, load_logs, extract_facts, validate_facts

client = OpenAI()


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


def display_neighbours(kg: KnowledgeGraph, entity: str):
    """Print all connections for an entity."""
    edges = kg.neighbours(entity)
    if not edges:
        print(f"  '{entity}' not found in graph.")
        return
    print(f"  {entity}:")
    for source, target, relation, confidence in edges:
        if source == entity:
            print(f"    --[{relation}]--> {target}  ({confidence:.2f})")
        else:
            print(f"    <--[{relation}]-- {source}  ({confidence:.2f})")


def main():
    print("Loading logs and extracting facts...")
    logs = load_logs()

    all_facts = []
    for log in logs:
        facts, _ = extract_facts(log["content"], client)
        validated = validate_facts(facts)
        all_facts.extend(validated)
        print(f"  {log['id']}: {len(validated)} facts")

    print(f"\nTotal: {len(all_facts)} validated facts.")
    print("Building graph...")
    kg = build_graph(all_facts)
    n_nodes = kg.graph.number_of_nodes()
    n_edges = kg.graph.number_of_edges()
    print(f"Graph ready: {n_nodes} entities, {n_edges} relationships.\n")
    print("Enter an entity name, a command, or 'quit'.\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/stats":
            density = nx.density(kg.graph)
            print(f"  Entities: {n_nodes} | Relationships: {n_edges} | Density: {density:.4f}")
            continue

        if user_input == "/entities":
            nodes = sorted(kg.graph.nodes())
            for node in nodes:
                degree = kg.graph.degree(node)
                print(f"  {node} ({degree} connections)")
            continue

        if user_input.startswith("/path "):
            parts = user_input[6:].split("->")
            if len(parts) != 2:
                print("  Usage: /path <from> -> <to>")
                continue
            start = parts[0].strip()
            end = parts[1].strip()
            path = kg.find_path(start, end)
            if path:
                print(f"  {' -> '.join(path)} ({len(path) - 1} hops)")
            else:
                print(f"  No path found between '{start}' and '{end}'.")
            continue

        if user_input.startswith("/related "):
            entity = user_input[9:].strip()
            edges = kg.find_connections(entity, max_hops=2)
            if edges:
                print(f"  Connections within 2 hops of '{entity}':")
                for source, target, relation, confidence in edges:
                    print(f"    {source} --[{relation}]--> {target}  ({confidence:.2f})")
            else:
                print(f"  '{entity}' not found or has no connections.")
            continue

        display_neighbours(kg, user_input)
        print()


if __name__ == "__main__":
    main()
