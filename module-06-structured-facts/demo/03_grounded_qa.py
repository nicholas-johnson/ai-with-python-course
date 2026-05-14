"""
Module 6 Demo — 03: Grounded QA
===================================
Answer questions from a knowledge graph with citations.

Run:  python module-06-structured-facts/demo/03_grounded_qa.py

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
    subject: str
    predicate: str
    object: str
    source_text: str
    confidence: float = Field(ge=0.0, le=1.0)


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
                    "Extract factual claims. Return JSON with 'facts' array.\n"
                    f"Schema:\n{schema_desc}\nBe precise. Rate confidence 0-1."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    facts_data = data.get("facts", []) if isinstance(data, dict) else data
    return [Fact.model_validate(item) for item in facts_data if isinstance(item, dict)]


def build_graph(facts: list[Fact]) -> nx.DiGraph:
    G = nx.DiGraph()
    for f in facts:
        G.add_edge(f.subject, f.object, relation=f.predicate, confidence=f.confidence)
    return G


def retrieve_evidence(G: nx.DiGraph, entities: list[str], max_hops: int = 2) -> list[dict]:
    evidence = []
    seen = set()
    for entity in entities:
        if entity not in G:
            continue
        visited = set()
        queue = [(entity, 0)]
        while queue:
            node, depth = queue.pop(0)
            if node in visited or depth > max_hops:
                continue
            visited.add(node)
            for _, target, data in G.out_edges(node, data=True):
                key = (node, target, data.get("relation"))
                if key not in seen:
                    seen.add(key)
                    evidence.append({
                        "source": node, "target": target,
                        "relation": data.get("relation", "?"),
                        "confidence": data.get("confidence", 0),
                    })
                if depth + 1 <= max_hops:
                    queue.append((target, depth + 1))
            for source, _, data in G.in_edges(node, data=True):
                key = (source, node, data.get("relation"))
                if key not in seen:
                    seen.add(key)
                    evidence.append({
                        "source": source, "target": node,
                        "relation": data.get("relation", "?"),
                        "confidence": data.get("confidence", 0),
                    })
                if depth + 1 <= max_hops:
                    queue.append((source, depth + 1))
    return evidence


def grounded_qa(question: str, G: nx.DiGraph) -> tuple[str, list[dict]]:
    """Answer a question grounded in graph evidence."""
    entity_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Extract entity names from the question. Return JSON: {\"entities\": [...]}"},
            {"role": "user", "content": question},
        ],
    )
    extracted = json.loads(entity_resp.choices[0].message.content).get("entities", [])

    nodes_lower = {n.lower(): n for n in G.nodes()}
    matched = []
    for e in extracted:
        e_lower = e.lower()
        if e_lower in nodes_lower:
            matched.append(nodes_lower[e_lower])
        else:
            for nl, no in nodes_lower.items():
                if e_lower in nl or nl in e_lower:
                    matched.append(no)
    matched = list(set(matched))

    evidence = retrieve_evidence(G, matched)
    if not evidence:
        return "No relevant facts found in the knowledge graph.", []

    fact_lines = []
    for i, e in enumerate(evidence[:15], 1):
        fact_lines.append(f"[Fact {i}] {e['source']} --{e['relation']}--> {e['target']} ({e['confidence']:.2f})")

    messages = [
        {"role": "system", "content": "Answer using ONLY the facts below. Cite as [Fact N]. If insufficient, say so."},
        {"role": "user", "content": "\n".join(fact_lines) + f"\n\nQuestion: {question}"},
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return resp.choices[0].message.content, evidence


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")


def main():
    section("Building Knowledge Graph")

    logs = load_logs()
    sample = logs[:10]
    print(f"  Extracting facts from {len(sample)} logs...")
    all_facts = []
    for log in sample:
        facts = extract_facts(log["content"])
        validated = [f for f in facts if f.confidence >= 0.7]
        all_facts.extend(validated)
        print(f"    {log['id']}: {len(validated)} facts")

    G = build_graph(all_facts)
    print(f"\n  Graph: {G.number_of_nodes()} entities, {G.number_of_edges()} relationships")

    pause()

    section("Part 1: Grounded QA")

    question = "What maintenance work has been done on the ship?"
    print(f"  Question: {question}\n")
    print("  Extracting entities, retrieving evidence, generating answer...\n")

    answer, evidence = grounded_qa(question, G)
    print(f"  Answer: {answer}\n")
    if evidence:
        print("  Evidence used:")
        for i, e in enumerate(evidence[:5], 1):
            print(f"    [{i}] {e['source']} --{e['relation']}--> {e['target']}  ({e['confidence']:.2f})")

    pause()

    section("Part 2: Without Graph (Comparison)")

    print(f"  Same question without graph evidence:\n")
    raw_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
    )
    print(f"  {raw_resp.choices[0].message.content}\n")
    print("  Notice: no citations, no grounding, possibly hallucinated details.")

    pause()

    section("Part 3: Ask Your Own Questions (Interactive)")

    print("  Enter a question, or 'quit' to exit.\n")

    while True:
        try:
            q = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() == "quit":
            break

        answer, evidence = grounded_qa(q, G)
        print(f"  Agent: {answer}")
        if evidence:
            print("\n  Facts:")
            for i, e in enumerate(evidence[:5], 1):
                print(f"    [{i}] {e['source']} --{e['relation']}--> {e['target']}")
        print()

    print("\n  Demo complete!")


if __name__ == "__main__":
    main()
