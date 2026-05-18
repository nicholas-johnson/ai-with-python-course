"""
Exercise 3 -- Solution
========================
Grounded QA from a knowledge graph with citations.

Run:  python solution.py
"""

import json
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI

from fact_extractor import load_logs, extract_facts, validate_facts
from graph_builder import build_graph, KnowledgeGraph

load_dotenv()

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


def build_graph_from_logs(client: OpenAI) -> KnowledgeGraph:
    """Load all ship logs, extract facts, validate, and build a knowledge graph."""
    logs = load_logs()
    all_facts = []
    for log in logs:
        facts, _ = extract_facts(log["content"], client)
        validated = validate_facts(facts)
        all_facts.extend(validated)
    return build_graph(all_facts)


def handle_repl_command(
    graph: KnowledgeGraph,
    client: OpenAI,
    cmd: str,
    args: str,
    last_question: str | None = None,
    last_evidence: list[dict] | None = None,
) -> int | None:
    """Dispatch a slash command. Returns new max_hops for /hops, else None."""
    if cmd == "/evidence":
        if last_evidence:
            print("\n  === Retrieved Evidence ===")
            display_evidence(last_evidence, brief=False)
            print()
        else:
            print("  No previous query. Ask a question first.")
        return None

    if cmd == "/nograph":
        if last_question:
            print("  (Without graph)")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": last_question}],
            )
            print(f"  {response.choices[0].message.content}\n")
        else:
            print("  No previous query. Ask a question first.")
        return None

    if cmd == "/hops":
        try:
            new_hops = int(args)
            print(f"  Traversal depth set to {new_hops} hops.\n")
            return new_hops
        except ValueError:
            print("  Usage: /hops <number>")
        return None

    return None


def main():
    print("Loading logs, extracting facts, and building graph...")
    graph = build_graph_from_logs(client)
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

        parts = user_input.split(" ", 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if cmd.startswith("/"):
            result = handle_repl_command(
                graph, client, cmd, args,
                last_question=last_question, last_evidence=last_evidence,
            )
            if cmd == "/hops" and result is not None:
                max_hops = result
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
