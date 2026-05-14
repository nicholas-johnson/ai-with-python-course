"""
Module 6 Demo — 01: Structured Extraction
=============================================
Extract structured facts from ship logs using OpenAI + Pydantic.

Run:  python module-06-structured-facts/demo/01_extraction.py

Requires: OPENAI_API_KEY environment variable.
"""

import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ship_logs.json"
client = OpenAI()


class Fact(BaseModel):
    subject: str = Field(description="The entity this fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


def load_logs() -> list[dict]:
    return json.loads(DATA_PATH.read_text())


def extract_facts(text: str) -> tuple[list[Fact], str]:
    """Extract facts from text. Returns (facts, raw_json)."""
    schema_desc = json.dumps(Fact.model_json_schema(), indent=2)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract every factual claim from the text. "
                    "Return a JSON object with a 'facts' key containing an array.\n"
                    f"Schema:\n{schema_desc}\n"
                    "Be precise. Include the exact source sentence. Rate confidence 0-1."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    facts_data = data.get("facts", []) if isinstance(data, dict) else data
    facts = []
    for item in facts_data:
        try:
            facts.append(Fact.model_validate(item))
        except Exception:
            continue
    return facts, raw


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")


def main():
    section("Part 1: The Pydantic Schema")

    print("  We define a Fact model with typed fields:\n")
    print(json.dumps(Fact.model_json_schema(), indent=2))
    print("\n  This schema tells the LLM exactly what structure to return.")
    print("  Pydantic validates the response -- malformed data raises errors.")

    pause()

    section("Part 2: Extract Facts from a Log")

    logs = load_logs()
    log = logs[0]
    print(f"  Log: {log['id']} ({log['author']})")
    print(f"  Content: {log['content'][:200]}...\n")

    print("  Calling OpenAI with response_format='json_object'...")
    facts, raw_json = extract_facts(log["content"])

    print(f"\n  Raw JSON response:\n")
    parsed = json.loads(raw_json)
    print(json.dumps(parsed, indent=2)[:500])
    print(f"\n  Parsed into {len(facts)} Fact objects:")
    for f in facts:
        print(f"    [{f.confidence:.2f}] {f.subject} --{f.predicate}--> {f.object}")

    pause()

    section("Part 3: Validation and Filtering")

    print("  Filtering facts with confidence < 0.7...")
    validated = [f for f in facts if f.confidence >= 0.7]
    print(f"  {len(facts)} raw -> {len(validated)} validated\n")
    for f in validated:
        print(f"    [{f.confidence:.2f}] {f.subject} --{f.predicate}--> {f.object}")

    pause()

    section("Part 4: Try Another Log (Interactive)")

    logs_by_id = {l["id"]: l for l in logs}
    print("  Enter a log ID to extract facts, or 'quit' to exit.")
    print(f"  Available: {', '.join(list(logs_by_id.keys())[:10])}...\n")

    while True:
        try:
            user_input = input("  Log ID: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() == "quit":
            break
        if user_input in logs_by_id:
            log = logs_by_id[user_input]
            print(f"  Extracting from {user_input}...")
            facts, _ = extract_facts(log["content"])
            for f in facts:
                print(f"    [{f.confidence:.2f}] {f.subject} --{f.predicate}--> {f.object}")
            print()
        else:
            print(f"  Unknown log ID: {user_input}")

    print("\n  Demo complete!")


if __name__ == "__main__":
    main()
