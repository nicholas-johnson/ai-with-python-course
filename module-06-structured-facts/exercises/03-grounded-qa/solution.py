"""
Exercise 3 -- Solution
========================
Grounded QA from a knowledge graph with citations.

Run:  python solution.py
"""

import json
from dataclasses import dataclass, field

from openai import OpenAI

from fact_extractor import load_logs, extract_facts, validate_facts
from graph_builder import build_graph, KnowledgeGraph

client = OpenAI()


@dataclass
class GroundedAnswer:
    question: str
    answer: str
    evidence: list[dict]
    confidence: float


def extract_query_entities(question: str, client: OpenAI, graph: KnowledgeGraph) -> list[str]:
    """Identify entity names from the question that exist in the graph."""
    graph_nodes = list(graph.graph.nodes())

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract entity names from the question that might appear in a knowledge graph. "
                    "Return a JSON object with an 'entities' key containing an array of strings. "
                    "Be generous -- include people, systems, locations, events, and concepts."
                ),
            },
            {"role": "user", "content": question},
        ],
    )

    data = json.loads(response.choices[0].message.content)
    extracted = data.get("entities", [])

    matched = []
    nodes_lower = {n.lower(): n for n in graph_nodes}
    for entity in extracted:
        entity_lower = entity.lower()
        if entity_lower in nodes_lower:
            matched.append(nodes_lower[entity_lower])
        else:
            for node_lower, node_original in nodes_lower.items():
                if entity_lower in node_lower or node_lower in entity_lower:
                    matched.append(node_original)

    return list(set(matched))


def retrieve_evidence(graph: KnowledgeGraph, entities: list[str], max_hops: int = 2) -> list[dict]:
    """Retrieve graph facts connected to the identified entities."""
    seen = set()
    evidence = []

    for entity in entities:
        edges = graph.find_connections(entity, max_hops)
        for source, target, relation, confidence in edges:
            key = (source, target, relation)
            if key not in seen:
                seen.add(key)
                evidence.append({
                    "source": source,
                    "target": target,
                    "relation": relation,
                    "confidence": confidence,
                })

    evidence.sort(key=lambda e: e["confidence"], reverse=True)
    return evidence


def build_grounded_prompt(question: str, evidence: list[dict]) -> list[dict]:
    """Build a grounded prompt with [Fact N] citations."""
    fact_lines = []
    for i, e in enumerate(evidence, 1):
        fact_lines.append(
            f"[Fact {i}] {e['source']} --{e['relation']}--> {e['target']} "
            f"(confidence: {e['confidence']:.2f})"
        )

    facts_text = "\n".join(fact_lines)

    return [
        {
            "role": "system",
            "content": (
                "Answer the question using ONLY the facts below. "
                "Cite facts using [Fact N]. "
                "If the facts don't contain the answer, say so. "
                "Include a confidence score (0-1) for your answer."
            ),
        },
        {
            "role": "user",
            "content": f"{facts_text}\n\nQuestion: {question}",
        },
    ]


def grounded_qa(
    question: str,
    graph: KnowledgeGraph,
    client: OpenAI,
    max_hops: int = 2,
) -> GroundedAnswer:
    """End-to-end grounded QA: extract entities, retrieve, prompt, generate."""
    entities = extract_query_entities(question, client, graph)

    if not entities:
        return GroundedAnswer(
            question=question,
            answer="I couldn't identify any relevant entities in your question.",
            evidence=[],
            confidence=0.0,
        )

    evidence = retrieve_evidence(graph, entities, max_hops)

    if not evidence:
        return GroundedAnswer(
            question=question,
            answer="No relevant facts found in the knowledge graph.",
            evidence=[],
            confidence=0.0,
        )

    messages = build_grounded_prompt(question, evidence)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    answer = response.choices[0].message.content

    avg_confidence = sum(e["confidence"] for e in evidence) / len(evidence)

    return GroundedAnswer(
        question=question,
        answer=answer,
        evidence=evidence,
        confidence=avg_confidence,
    )


def display_evidence(evidence: list[dict], brief: bool = False):
    """Print evidence facts."""
    for i, e in enumerate(evidence, 1):
        if brief:
            print(f"    [{i}] {e['source']} --{e['relation']}--> {e['target']}  ({e['confidence']:.2f})")
        else:
            print(f"\n  [Fact {i}]")
            print(f"  {e['source']} --{e['relation']}--> {e['target']}")
            print(f"  Confidence: {e['confidence']:.2f}")


def main():
    print("Loading logs, extracting facts, and building graph...")
    logs = load_logs()

    all_facts = []
    for log in logs:
        facts, _ = extract_facts(log["content"], client)
        validated = validate_facts(facts)
        all_facts.extend(validated)

    graph = build_graph(all_facts)
    n_nodes = graph.graph.number_of_nodes()
    n_edges = graph.graph.number_of_edges()
    print(f"Graph ready: {n_nodes} entities, {n_edges} relationships.")
    print("Ask a question, or type a command (/evidence, /nograph, /hops <n>), or 'quit'.\n")

    max_hops = 2
    last_question = None
    last_evidence = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/evidence":
            if last_evidence:
                print("\n  === Retrieved Evidence ===")
                display_evidence(last_evidence, brief=False)
                print()
            else:
                print("  No previous query. Ask a question first.")
            continue

        if user_input == "/nograph":
            if last_question:
                print("  (Without graph)")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": last_question}],
                )
                print(f"  {response.choices[0].message.content}\n")
            else:
                print("  No previous query. Ask a question first.")
            continue

        if user_input.startswith("/hops "):
            try:
                max_hops = int(user_input.split(" ", 1)[1])
                print(f"  Traversal depth set to {max_hops} hops.\n")
            except ValueError:
                print("  Usage: /hops <number>")
            continue

        last_question = user_input
        result = grounded_qa(user_input, graph, client, max_hops)
        last_evidence = result.evidence

        print(f"Agent: {result.answer}")
        if result.evidence:
            print("\n  Facts used:")
            display_evidence(result.evidence, brief=True)
        print()


if __name__ == "__main__":
    main()
