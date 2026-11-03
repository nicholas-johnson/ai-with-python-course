"""
Module 6 Demo — Knowledge graph MCP server
==========================================
Serves the saved Pathfinder graph over stdio. No model call in this process.

graph.json is the extract → validate → store pipeline, already stored:
the same subject / predicate / object / confidence / source text as demo 01,
with one canonical name per entity.

Run directly:  python graph_server.py          (MCP stdio server)
Inspect:       mcp dev graph_server.py         (browser UI)
Used by:       04_graph_agent.py, which spawns this file.

Do not print to stdout. MCP uses stdout for the protocol.
"""

import json
import sys
from pathlib import Path

import networkx as nx
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

GRAPH_PATH = Path(__file__).resolve().parent / "graph.json"
MAX_HOPS = 3
MAX_FACTS = 30

server = MCPServer("Pathfinder Graph")


class StoredFact(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_id: str
    source_text: str


def load_graph() -> nx.MultiDiGraph:
    raw = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    facts = [StoredFact.model_validate(item) for item in raw]
    built = nx.MultiDiGraph()
    for fact in facts:
        built.add_edge(
            fact.subject,
            fact.object,
            relation=fact.predicate,
            confidence=fact.confidence,
            source_id=fact.source_id,
            source_text=fact.source_text,
        )
    return built


graph = load_graph()


def _triple(subject: str, obj: str, data: dict) -> dict:
    return {
        "subject": subject,
        "predicate": data["relation"],
        "object": obj,
        "confidence": data["confidence"],
        "source_id": data["source_id"],
        "source_text": data["source_text"],
    }


def _edges_between(left: str, right: str) -> list[tuple[str, str, dict]]:
    found = []
    if graph.has_edge(left, right):
        found.extend((left, right, data) for data in graph.get_edge_data(left, right).values())
    if graph.has_edge(right, left):
        found.extend((right, left, data) for data in graph.get_edge_data(right, left).values())
    return found


def resolve_entity(name: str) -> tuple[str | None, dict | None]:
    """Match a name to one node. Exact, then a unique substring, else an error."""
    query = name.strip()
    if not query:
        return None, {"error": "entity is required"}

    by_lower = {node.lower(): node for node in graph.nodes}
    exact = by_lower.get(query.lower())
    if exact:
        return exact, None

    needle = query.lower()
    matches = [node for node in sorted(graph.nodes) if needle in node.lower()]
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, {
            "error": "not_found",
            "query": query,
            "hint": "Call list_entities to see names.",
        }
    return None, {"error": "ambiguous", "query": query, "matches": matches}


def entity_list(query: str = "") -> dict:
    needle = query.strip().lower()
    names = sorted(graph.nodes, key=str.lower)
    if needle:
        names = [name for name in names if needle in name.lower()]
    return {
        "count": len(names),
        "entities": [{"name": name, "connections": graph.degree(name)} for name in names],
    }


def neighbour_facts(entity: str) -> dict:
    node, error = resolve_entity(entity)
    if error:
        return error
    facts = []
    for _, target, data in graph.out_edges(node, data=True):
        facts.append(_triple(node, target, data))
    for source, _, data in graph.in_edges(node, data=True):
        facts.append(_triple(source, node, data))
    facts.sort(key=lambda fact: (
        fact["predicate"],
        fact["subject"].lower(),
        fact["object"].lower(),
    ))
    return {"entity": node, "count": len(facts), "facts": facts}


def path_between(start: str, end: str) -> dict:
    start_node, error = resolve_entity(start)
    if error:
        return error
    end_node, error = resolve_entity(end)
    if error:
        return error
    if start_node == end_node:
        return {"start": start_node, "end": end_node, "hops": 0, "path": [start_node], "facts": []}

    try:
        nodes = nx.shortest_path(graph.to_undirected(), start_node, end_node)
    except nx.NetworkXNoPath:
        return {
            "start": start_node,
            "end": end_node,
            "path": None,
            "message": "No path between these entities.",
        }

    facts = []
    for step, (left, right) in enumerate(zip(nodes, nodes[1:]), start=1):
        for subject, obj, data in _edges_between(left, right):
            facts.append({"step": step, **_triple(subject, obj, data)})
    return {
        "start": start_node,
        "end": end_node,
        "hops": len(nodes) - 1,
        "path": nodes,
        "facts": facts,
    }


def facts_within(entity: str, hops: int = 1) -> dict:
    node, error = resolve_entity(entity)
    if error:
        return error
    hops = max(1, min(int(hops), MAX_HOPS))
    lengths = nx.single_source_shortest_path_length(graph.to_undirected(), node, cutoff=hops)

    seen = set()
    facts = []
    for current in sorted(lengths, key=lambda name: (lengths[name], name.lower())):
        incident = []
        for _, target, data in graph.out_edges(current, data=True):
            incident.append((current, target, data))
        for source, _, data in graph.in_edges(current, data=True):
            incident.append((source, current, data))
        for subject, obj, data in incident:
            key = (subject, obj, data["relation"], data["source_id"])
            if key in seen:
                continue
            seen.add(key)
            distance = min(
                lengths[subject] if subject in lengths else hops,
                lengths[obj] if obj in lengths else hops,
            )
            facts.append({"hops": distance, **_triple(subject, obj, data)})

    facts.sort(key=lambda fact: (fact["hops"], fact["subject"].lower(), fact["predicate"]))
    truncated = len(facts) > MAX_FACTS
    kept = facts[:MAX_FACTS]
    return {
        "entity": node,
        "hops": hops,
        "count": len(kept),
        "truncated": truncated,
        "facts": kept,
    }


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


@server.tool()
def list_entities(query: str = "") -> str:
    """List entity names in the knowledge graph.

    query: optional substring, case-insensitive. Empty returns every entity.
    Call this when you are not sure of the exact name.
    """
    return _dump(entity_list(query))


@server.tool()
def neighbours(entity: str) -> str:
    """Return the facts directly connected to one entity, in either direction.

    entity: exact name, or a substring that matches one entity.
    If several names match, the tool returns the candidates and does not guess.
    """
    return _dump(neighbour_facts(entity))


@server.tool()
def shortest_path(start: str, end: str) -> str:
    """Shortest chain of facts connecting two entities, ignoring edge direction.

    Use this for "how is X related to Y?". Each hop includes the source log id
    and the sentence it came from. Names follow the same rules as neighbours.
    """
    return _dump(path_between(start, end))


@server.tool()
def facts_about(entity: str, hops: int = 1) -> str:
    """Return facts within `hops` of an entity.

    hops: 1, 2, or 3. hops=1 is the immediate neighbourhood.
    Use this for "what do we know about X?", not for a path between two names.
    """
    return _dump(facts_within(entity, hops))


if __name__ == "__main__":
    print(
        f"Graph MCP server: {graph.number_of_nodes()} entities, "
        f"{graph.number_of_edges()} facts",
        file=sys.stderr,
        flush=True,
    )
    server.run()
