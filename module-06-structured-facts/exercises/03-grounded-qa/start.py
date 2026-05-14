"""
Exercise 3: Grounded QA
==========================
Answer questions from a knowledge graph with source citations.

Run:  python start.py
"""

from dataclasses import dataclass, field

from graph_builder import KnowledgeGraph

# TODO: import OpenAI from openai
# TODO: import load_logs, extract_facts, validate_facts from fact_extractor
# TODO: import build_graph from graph_builder


@dataclass
class GroundedAnswer:
    question: str
    answer: str
    evidence: list[dict]
    confidence: float


# TODO: Implement extract_query_entities(question, client, graph) -> list[str]
#   Identify entity names from the question that exist in the graph.
#   Approach: ask OpenAI to extract entity names, then match against graph nodes.
#   Return a list of matching node names.


# TODO: Implement retrieve_evidence(graph, entities, max_hops) -> list[dict]
#   For each entity, call graph.find_connections(entity, max_hops).
#   Collect unique edges as dicts: {source, target, relation, confidence}
#   Return the collected evidence.


# TODO: Implement build_grounded_prompt(question, evidence) -> list[dict]
#   Build a system + user message pair where:
#   - system: instructs the LLM to answer ONLY from the facts, citing [Fact N]
#   - user: contains numbered facts and the question
#   Return a list of message dicts.


# TODO: Implement grounded_qa(question, graph, client) -> GroundedAnswer
#   1. extract_query_entities to find relevant entities
#   2. retrieve_evidence to get graph facts
#   3. build_grounded_prompt
#   4. Call OpenAI chat.completions.create
#   5. Return a GroundedAnswer


def main():
    print("Loading logs, extracting facts, and building graph...")

    # TODO: Build the graph from all logs
    # TODO: Interactive loop:
    #   - question -> grounded_qa, display answer + evidence summary
    #   - /evidence -> show full evidence from last query
    #   - /nograph -> re-ask last question without graph evidence
    #   - /hops <n> -> change max_hops
    #   - quit -> break

    print("TODO: implement the QA functions, then uncomment the loop.")


if __name__ == "__main__":
    main()
