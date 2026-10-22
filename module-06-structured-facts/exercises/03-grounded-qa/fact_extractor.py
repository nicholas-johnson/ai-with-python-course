"""
Fact extractor -- provided from Exercise 1 solution.
Import this to get load_logs, extract_facts, validate_facts, and the Fact model.
"""

import json
import os
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "derelict_logs.json"


class Fact(BaseModel):
    subject: str = Field(description="The entity this fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


def load_logs() -> list[dict]:
    """Load salvage logs from the data directory."""
    return json.loads(DATA_PATH.read_text())


class FactList(BaseModel):
    facts: list[Fact]


def extract_facts(text: str, client: OpenAI) -> tuple[list[Fact], str]:
    """Extract structured facts from text using OpenAI. Returns (facts, raw_json)."""
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=FactList,
        input=[
            {
                "role": "system",
                "content": (
                    "Extract every factual claim from the text. "
                    "Be precise with subject/predicate/object triples. "
                    "Include the exact source sentence. "
                    "Rate confidence from 0.0 to 1.0."
                ),
            },
            {"role": "user", "content": text},
        ],
    )

    if response.output_parsed is None:
        return [], ""
    return response.output_parsed.facts, response.output_text


def validate_facts(facts: list[Fact], min_confidence: float = 0.7) -> list[Fact]:
    """Filter low-confidence facts and deduplicate by (subject, predicate, object)."""
    above_threshold = [f for f in facts if f.confidence >= min_confidence]

    best: dict[tuple[str, str, str], Fact] = {}
    for fact in above_threshold:
        key = (fact.subject.lower(), fact.predicate.lower(), fact.object.lower())
        if key not in best or fact.confidence > best[key].confidence:
            best[key] = fact

    return list(best.values())
