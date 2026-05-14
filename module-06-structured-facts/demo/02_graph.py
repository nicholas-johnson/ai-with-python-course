"""
Module 6 Demo — 02: Knowledge Graph
=======================================
Build a knowledge graph from extracted facts and explore it.

Run:  python module-06-structured-facts/demo/02_graph.py

Requires: OPENAI_API_KEY environment variable.
"""

import json
from pathlib import Path

import networkx as nx
from openai import OpenAI
from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ship_logs.json"
client = OpenAI()


class Fact(BaseModel):
    subject: str = Field(description="The entity this fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


def load_logs() -> list[dict]:
    return json.loads(DATA_PATH.read_text())


def extract_facts(text: str) -> list[Fact]:
    schema_desc = json.dumps(Fact.model_json_schema(), indent=2)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract every factual claim. Return JSON with a 'facts' array.\n"
                    f"Schema:\n{schema_desc}\nBe precise. Rate confidence 0-1."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    facts_data = data.get("facts", []) if isinstance(data, dict) else data
    facts = []
    for item in facts_data:
        try:
            facts.append(Fact.model_validate(item))
        except Exception:
            continue
    return [f for f in facts if f.confidence >= 0.7]


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")


def main():
    section("Part 1: Extract Facts from Ship Logs")

    logs = load_logs()
    sample = logs[:8]
    print(f"  Extracting facts from {len(sample)} logs...")

    all_facts = []
    for log in sample:
        facts = extract_facts(log["content"])
        all_facts.extend(facts)
        print(f"    {log['id']}: {len(facts)} facts")

    print(f"\n  Total: {len(all_facts)} validated facts")

    pause()

    section("Part 2: Build the Graph")

    G = nx.DiGraph()
    for f in all_facts:
        G.add_node(f.subject)
        G.add_node(f.object)
        G.add_edge(f.subject, f.object, relation=f.predicate, confidence=f.confidence)

    print(f"  Nodes (entities): {G.number_of_nodes()}")
    print(f"  Edges (relationships): {G.number_of_edges()}")
    print(f"  Density: {nx.density(G):.4f}\n")

    print("  Top entities by degree:")
    degrees = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
    for node, degree in degrees:
        print(f"    {node}: {degree} connections")

    pause()

    section("Part 3: Query the Graph")

    entity = degrees[0][0] if degrees else "unknown"
    print(f"  Neighbours of '{entity}':\n")
    for _, target, data in G.out_edges(entity, data=True):
        print(f"    --[{data.get('relation', '?')}]--> {target}")
    for source, _, data in G.in_edges(entity, data=True):
        print(f"    <--[{data.get('relation', '?')}]-- {source}")

    if len(degrees) >= 2:
        start = degrees[0][0]
        end = degrees[1][0]
        try:
            path = nx.shortest_path(G, start, end)
            print(f"\n  Shortest path {start} -> {end}:")
            print(f"    {' -> '.join(path)} ({len(path) - 1} hops)")
        except nx.NetworkXNoPath:
            print(f"\n  No path between {start} and {end}")

    pause()

    section("Part 4: Explore (Interactive)")

    nodes_lower = {n.lower(): n for n in G.nodes()}
    print("  Enter an entity name to see connections, or 'quit' to exit.")
    print(f"  Some entities: {', '.join(list(G.nodes())[:8])}...\n")

    while True:
        try:
            user_input = input("  Entity: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() == "quit":
            break

        entity = nodes_lower.get(user_input.lower())
        if entity:
            for _, target, data in G.out_edges(entity, data=True):
                print(f"    --[{data.get('relation', '?')}]--> {target}")
            for source, _, data in G.in_edges(entity, data=True):
                print(f"    <--[{data.get('relation', '?')}]-- {source}")
            print()
        else:
            print(f"    '{user_input}' not in graph.")

    print("\n  Demo complete!")


if __name__ == "__main__":
    main()
