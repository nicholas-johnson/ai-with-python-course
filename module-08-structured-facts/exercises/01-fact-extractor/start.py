"""Exercise 01 — Fact Extractor

Extract structured facts from unstructured ship log text.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Fact(BaseModel):
    subject: str = Field(description="The entity the fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this fact was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


def build_extraction_prompt(text: str) -> str:
    """Return the prompt that asks the LLM to extract facts as JSON."""
    # TODO: build a prompt that instructs the LLM to return a JSON array
    # of facts matching the Fact schema above.
    raise NotImplementedError


def parse_llm_response(raw_json: str) -> list[Fact]:
    """Parse the raw JSON string from the LLM into a list of Fact objects."""
    # TODO: parse the JSON and return validated Fact instances.
    raise NotImplementedError


def extract_facts(text: str, llm_call) -> list[Fact]:
    """End-to-end extraction: build prompt, call LLM, parse response."""
    # TODO: combine build_extraction_prompt, llm_call, and parse_llm_response.
    raise NotImplementedError


def validate_facts(facts: list[Fact], min_confidence: float = 0.7) -> list[Fact]:
    """Filter low-confidence facts and deduplicate by (subject, predicate, object)."""
    # TODO: drop facts below min_confidence, keep highest-confidence duplicate.
    raise NotImplementedError
