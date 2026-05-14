"""
Exercise 2: Knowledge Graph
==============================
Build a knowledge graph from extracted facts and query it interactively.

Run:  python start.py
"""

import networkx as nx

from fact_extractor import Fact

# TODO: import load_logs, extract_facts, validate_facts from fact_extractor
# TODO: import OpenAI from openai


class KnowledgeGraph:
    """Knowledge graph wrapping a networkx DiGraph."""

    def __init__(self):
        self.graph = nx.DiGraph()

    # TODO: Implement add_fact(fact: Fact)
    #   Add subject and object as nodes (with metadata if available).
    #   Add an edge from subject to object with the predicate as the relation
    #   and confidence as a weight.

    # TODO: Implement neighbours(entity: str) -> list[tuple]
    #   Return all edges connected to the entity (both incoming and outgoing).
    #   Each tuple: (source, target, relation, confidence)

    # TODO: Implement find_path(start: str, end: str) -> list[str] | None
    #   Return the shortest path between two entities, or None if no path exists.

    # TODO: Implement find_connections(entity: str, max_hops: int = 2) -> list[tuple]
    #   BFS from the entity, return all edges within max_hops.


# TODO: Implement build_graph(facts: list[Fact]) -> KnowledgeGraph
#   Create a KnowledgeGraph, call add_fact for each fact, return the graph.


def main():
    print("Loading logs and extracting facts...")

    # TODO: Load logs, extract and validate facts from all logs
    # TODO: Build the graph
    # TODO: Interactive loop:
    #   - entity name -> show neighbours
    #   - /path <from> -> <to> -> find_path
    #   - /stats -> node count, edge count, density
    #   - /entities -> list all nodes
    #   - /related <entity> -> find_connections with max_hops=2
    #   - quit -> break

    print("TODO: implement KnowledgeGraph and build_graph, then uncomment the loop.")


if __name__ == "__main__":
    main()
