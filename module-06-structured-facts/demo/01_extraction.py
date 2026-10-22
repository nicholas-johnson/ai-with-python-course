"""
Module 6 Demo — 01: Structured Extraction
=============================================
Extract structured facts from ship logs using OpenAI + Pydantic.

Run:  python module-06-structured-facts/demo/01_extraction.py

Requires: OPENAI_API_KEY environment variable.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

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


class FactList(BaseModel):
    facts: list[Fact]


def extract_facts(text: str) -> tuple[list[Fact], str]:
    """Extract facts from text. Returns (facts, raw_json)."""
    response = client.chat.completions.parse(
        model=MODEL,
        reasoning_effort="none",
        response_format=FactList,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract every factual claim from the text. "
                    "Be precise. Include the exact source sentence. Rate confidence 0-1."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    message = response.choices[0].message
    if message.refusal:
        return [], ""
    return message.parsed.facts, message.content


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
    print("\n  We pass the model itself as response_format. The SDK turns it into a")
    print("  strict JSON schema, the API constrains generation to that schema, and")
    print("  the SDK validates the reply back into Fact objects.")

    pause()

    section("Part 2: Extract Facts from a Log")

    logs = load_logs()
    log = logs[0]
    print(f"  Log: {log['id']} ({log['author']})")
    print(f"  Content: {log['content'][:200]}...\n")

    print("  Calling client.chat.completions.parse(response_format=FactList)...")
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
