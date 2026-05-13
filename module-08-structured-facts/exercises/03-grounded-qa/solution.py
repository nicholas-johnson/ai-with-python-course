"""Exercise 03 — Grounded QA (solution)"""

from __future__ import annotations

import json
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
    question_lower = question.lower()
    evidence: list[dict] = []

    for name, entity in graph.entities.items():
        if name.lower() in question_lower:
            for rel in graph.neighbours(name):
                text = f"{rel.source} --[{rel.relation}]--> {rel.target}"
                evidence.append({
                    "source_id": f"graph:{rel.source}:{rel.relation}:{rel.target}",
                    "text": text,
                    "relevance": 0.9,
                })

    seen = set()
    unique: list[dict] = []
    for e in evidence:
        if e["source_id"] not in seen:
            seen.add(e["source_id"])
            unique.append(e)

    return unique[:top_k]


def build_grounded_prompt(question: str, evidence: list[dict]) -> str:
    evidence_block = "\n".join(
        f"[{e['source_id']}] {e['text']}" for e in evidence
    )
    return (
        "Answer the question using ONLY the evidence provided. "
        "Cite sources by their IDs. Include a confidence score 0-1.\n"
        "Return JSON: {\"answer\": \"...\", \"citations\": [\"source_id\", ...], \"confidence\": 0.X}\n\n"
        f"Evidence:\n{evidence_block}\n\n"
        f"Question: {question}"
    )


def grounded_qa(
    question: str,
    graph: KnowledgeGraph,
    llm_call,
) -> GroundedAnswer:
    evidence = retrieve_relevant(graph, question)

    if not evidence:
        return GroundedAnswer(
            question=question,
            answer="Insufficient data to answer this question.",
            citations=[],
            confidence=0.0,
        )

    prompt = build_grounded_prompt(question, evidence)
    raw = llm_call(prompt)
    data = json.loads(raw)

    citations = []
    for sid in data.get("citations", []):
        matching = [e for e in evidence if e["source_id"] == sid]
        text = matching[0]["text"] if matching else ""
        relevance = matching[0]["relevance"] if matching else 0.0
        citations.append(Citation(source_id=sid, text=text, relevance=relevance))

    return GroundedAnswer(
        question=question,
        answer=data["answer"],
        citations=citations,
        confidence=data.get("confidence", 0.0),
    )
