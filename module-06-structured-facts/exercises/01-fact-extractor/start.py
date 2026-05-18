"""
Exercise 1: Fact Extractor
============================
Extract structured facts from salvage logs using OpenAI and Pydantic.

Run:  python start.py
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field

# TODO: import OpenAI from openai

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


# TODO: Implement extract_facts(text, client) -> list[Fact]
#   1. Build a prompt instructing the LLM to extract facts as JSON
#      matching the Fact schema (subject, predicate, object, source_text, confidence)
#   2. Call client.chat.completions.create with response_format={"type": "json_object"}
#   3. Parse the JSON response into a list of Fact objects
#   Return a list of validated Fact instances.


# TODO: Implement validate_facts(facts, min_confidence) -> list[Fact]
#   1. Filter out facts with confidence < min_confidence
#   2. Deduplicate by (subject, predicate, object), keeping highest confidence
#   Return the filtered list.


def main():
    print("Loading salvage logs...")
    logs = load_logs()
    logs_by_id = {log["id"]: log for log in logs}
    print(f"Loaded {len(logs)} logs.\n")

    # TODO: Create OpenAI client
    # client = OpenAI()

    # TODO: Interactive loop
    #   - Log ID (e.g. SAL-001) -> extract_facts from that log, display results
    #   - /all -> extract from all logs, show summary
    #   - /validate -> show validated facts from last extraction
    #   - /json -> show raw JSON from last LLM response
    #   - /schema -> print Fact.model_json_schema()
    #   - quit -> break

    print("TODO: implement extract_facts and validate_facts, then uncomment the loop.")


if __name__ == "__main__":
    main()
