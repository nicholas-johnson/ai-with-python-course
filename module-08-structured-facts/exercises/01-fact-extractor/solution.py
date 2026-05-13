"""Exercise 01 — Fact Extractor (solution)"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field


class Fact(BaseModel):
    subject: str = Field(description="The entity the fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this fact was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


def build_extraction_prompt(text: str) -> str:
    return (
        "Extract every factual claim from the text below. "
        "Return a JSON array of objects with keys: "
        "subject, predicate, object, source_text, confidence (0-1).\n\n"
        f"Text:\n{text}"
    )


def parse_llm_response(raw_json: str) -> list[Fact]:
    data = json.loads(raw_json)
    if isinstance(data, dict) and "facts" in data:
        data = data["facts"]
    return [Fact.model_validate(item) for item in data]


def extract_facts(text: str, llm_call) -> list[Fact]:
    prompt = build_extraction_prompt(text)
    raw = llm_call(prompt)
    return parse_llm_response(raw)


def validate_facts(facts: list[Fact], min_confidence: float = 0.7) -> list[Fact]:
    above_threshold = [f for f in facts if f.confidence >= min_confidence]

    best: dict[tuple[str, str, str], Fact] = {}
    for fact in above_threshold:
        key = (fact.subject, fact.predicate, fact.object)
        if key not in best or fact.confidence > best[key].confidence:
            best[key] = fact

    return list(best.values())
