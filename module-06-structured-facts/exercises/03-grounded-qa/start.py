"""
Exercise 3: Grounded QA
==========================
Answer questions from a knowledge graph with source citations.

Run:  python start.py
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


# ---------------------------------------------------------------------------
# TODO: Implement extract_query_entities(question, client, graph) -> list[str]
#   Identify entity names from the question that exist in the graph.
#   Approach: ask OpenAI to extract entity names, then match against graph nodes.
#   Return a list of matching node names.
# ---------------------------------------------------------------------------

def extract_query_entities(question: str, client: OpenAI, graph: KnowledgeGraph) -> list[str]:
    raise NotImplementedError("TODO: extract entities from question and match to graph nodes")


# ---------------------------------------------------------------------------
# TODO: Implement retrieve_evidence(graph, entities, max_hops) -> list[dict]
#   For each entity, call graph.find_connections(entity, max_hops).
#   Collect unique edges as dicts: {source, target, relation, confidence}
#   Return the collected evidence sorted by confidence.
# ---------------------------------------------------------------------------

def retrieve_evidence(graph: KnowledgeGraph, entities: list[str], max_hops: int = 2) -> list[dict]:
    raise NotImplementedError("TODO: gather unique edges from graph for given entities")


# ---------------------------------------------------------------------------
# TODO: Implement build_grounded_prompt(question, evidence) -> list[dict]
#   Build a system + user message pair where:
#   - system: instructs the LLM to answer ONLY from the facts, citing [Fact N]
#   - user: contains numbered facts and the question
#   Return a list of message dicts.
# ---------------------------------------------------------------------------

def build_grounded_prompt(question: str, evidence: list[dict]) -> list[dict]:
    raise NotImplementedError("TODO: build system + user messages from question and evidence")


# ---------------------------------------------------------------------------
# TODO: Implement grounded_qa(question, graph, client, max_hops) -> GroundedAnswer
#   1. extract_query_entities to find relevant entities
#   2. retrieve_evidence to get graph facts
#   3. build_grounded_prompt
#   4. Call OpenAI chat.completions.create
#   5. Return a GroundedAnswer
# ---------------------------------------------------------------------------

def grounded_qa(
    question: str,
    graph: KnowledgeGraph,
    client: OpenAI,
    max_hops: int = 2,
) -> GroundedAnswer:
    raise NotImplementedError("TODO: end-to-end grounded QA pipeline")


# ---------------------------------------------------------------------------
# Display and REPL helpers (complete)
# ---------------------------------------------------------------------------

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
