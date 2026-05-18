"""
Exercise 2: Knowledge Graph
==============================
Build a knowledge graph from extracted facts and query it interactively.

Run:  python start.py
"""

import networkx as nx
from dotenv import load_dotenv
from openai import OpenAI

from fact_extractor import Fact, load_logs, extract_facts, validate_facts

load_dotenv()

client = OpenAI()


class KnowledgeGraph:
    """Knowledge graph wrapping a networkx DiGraph."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_fact(self, fact: Fact):
        """Add a fact as nodes + edge in the graph."""
        raise NotImplementedError("TODO: add subject/object as nodes and predicate as edge")

    def neighbours(self, entity: str) -> list[tuple]:
        """Return all edges connected to the entity (incoming + outgoing)."""
        raise NotImplementedError("TODO: return (source, target, relation, confidence) tuples")

    def find_path(self, start: str, end: str) -> list[str] | None:
        """Find shortest path between two entities."""
        raise NotImplementedError("TODO: use nx.shortest_path")

    def find_connections(self, entity: str, max_hops: int = 2) -> list[tuple]:
        """BFS from entity, return all edges within max_hops."""
        raise NotImplementedError("TODO: BFS returning (source, target, relation, confidence) tuples")


def build_graph(facts: list[Fact]) -> KnowledgeGraph:
    """Build a knowledge graph from a list of Facts."""
    raise NotImplementedError("TODO: create KnowledgeGraph, add each fact, return it")


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


def ingest_facts_from_logs(client: OpenAI) -> KnowledgeGraph:
    """Load all salvage logs, extract and validate facts, build a knowledge graph."""
    raise NotImplementedError("TODO: load logs, extract/validate facts, build and return graph")


def handle_repl_command(kg: KnowledgeGraph, cmd: str, args: str) -> bool:
    """Dispatch a slash command. Returns True if the command was handled."""
    raise NotImplementedError("TODO: handle /stats, /entities, /path, /related commands")


def main():
    print("Loading logs and extracting facts...")
    kg = ingest_facts_from_logs(client)
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

        parts = user_input.split(" ", 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if cmd.startswith("/") and handle_repl_command(kg, cmd, args):
            continue

        display_neighbours(kg, user_input)
        print()


if __name__ == "__main__":
    main()
