"""Exercise 03 — Grounded QA

Answer questions from a knowledge graph with source citations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    name: str
    entity_type: str
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class Relationship:
    source: str
    target: str
    relation: str
    metadata: dict[str, str] = field(default_factory=dict)


class KnowledgeGraph:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.edges: list[Relationship] = []

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.name] = entity

    def add_relationship(self, rel: Relationship) -> None:
        self.edges.append(rel)

    def neighbours(self, name: str) -> list[Relationship]:
        return [e for e in self.edges if e.source == name or e.target == name]


@dataclass
class Citation:
    source_id: str
    text: str
    relevance: float


@dataclass
class GroundedAnswer:
    question: str
    answer: str
    citations: list[Citation]
    confidence: float


def retrieve_relevant(
    graph: KnowledgeGraph,
    question: str,
    top_k: int = 5,
) -> list[dict]:
    """Find entities and relationships in the graph relevant to the question.

    Return a list of evidence dicts with keys: source_id, text, relevance.
    Use simple keyword matching against entity names and relationship labels.
    """
    # TODO
    raise NotImplementedError


def build_grounded_prompt(question: str, evidence: list[dict]) -> str:
    """Build a prompt that asks the LLM to answer using the provided evidence.

    The prompt should instruct the model to cite sources by source_id and
    include a confidence score.
    """
    # TODO
    raise NotImplementedError


def grounded_qa(
    question: str,
    graph: KnowledgeGraph,
    llm_call,
) -> GroundedAnswer:
    """End-to-end grounded QA: retrieve evidence, prompt LLM, parse answer.

    If no evidence is found, return a GroundedAnswer with confidence=0.0.
    """
    # TODO
    raise NotImplementedError
