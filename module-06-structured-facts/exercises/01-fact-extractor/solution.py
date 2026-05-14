"""
Exercise 1 -- Solution
========================
Extract structured facts from ship logs using OpenAI and Pydantic.

Run:  python solution.py
"""

import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ship_logs.json"
client = OpenAI()


class Fact(BaseModel):
    subject: str = Field(description="The entity this fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


def load_logs() -> list[dict]:
    """Load ship logs from the data directory."""
    return json.loads(DATA_PATH.read_text())


def extract_facts(text: str, client: OpenAI) -> tuple[list[Fact], str]:
    """Extract structured facts from text using OpenAI. Returns (facts, raw_json)."""
    schema_desc = json.dumps(Fact.model_json_schema(), indent=2)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract every factual claim from the text. "
                    "Return a JSON object with a 'facts' key containing an array of objects.\n"
                    f"Each object must match this schema:\n{schema_desc}\n"
                    "Be precise with subject/predicate/object triples. "
                    "Include the exact source sentence. "
                    "Rate confidence from 0.0 to 1.0."
                ),
            },
            {"role": "user", "content": text},
        ],
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)
    facts_data = data.get("facts", data) if isinstance(data, dict) else data
    if isinstance(facts_data, dict):
        facts_data = [facts_data]

    facts = []
    for item in facts_data:
        try:
            facts.append(Fact.model_validate(item))
        except Exception:
            continue

    return facts, raw_json


def validate_facts(facts: list[Fact], min_confidence: float = 0.7) -> list[Fact]:
    """Filter low-confidence facts and deduplicate by (subject, predicate, object)."""
    above_threshold = [f for f in facts if f.confidence >= min_confidence]

    best: dict[tuple[str, str, str], Fact] = {}
    for fact in above_threshold:
        key = (fact.subject.lower(), fact.predicate.lower(), fact.object.lower())
        if key not in best or fact.confidence > best[key].confidence:
            best[key] = fact

    return list(best.values())


def display_facts(facts: list[Fact]):
    """Print facts in a readable format."""
    for f in facts:
        print(f"  [{f.confidence:.2f}] {f.subject} --{f.predicate}--> {f.object}")


def main():
    print("Loading ship logs...")
    logs = load_logs()
    logs_by_id = {log["id"]: log for log in logs}
    print(f"Loaded {len(logs)} logs.")
    print("Enter a log ID (e.g. LOG-001), a command, or 'quit'.\n")

    last_facts: list[Fact] = []
    last_raw_json: str = ""

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/schema":
            print(json.dumps(Fact.model_json_schema(), indent=2))
            continue

        if user_input == "/json":
            if last_raw_json:
                print(f"\n  === Raw LLM Response ===")
                print(last_raw_json)
                print()
            else:
                print("  No previous extraction. Enter a log ID first.")
            continue

        if user_input == "/validate":
            if last_facts:
                validated = validate_facts(last_facts)
                print(f"\n  {len(validated)} validated facts (threshold=0.7):")
                display_facts(validated)
                print()
            else:
                print("  No previous extraction. Enter a log ID first.")
            continue

        if user_input == "/all":
            print("Extracting facts from all logs...")
            all_facts = []
            for log in logs:
                facts, _ = extract_facts(log["content"], client)
                all_facts.extend(facts)
                print(f"  {log['id']}: {len(facts)} facts")
            validated = validate_facts(all_facts)
            print(f"\n  Total: {len(all_facts)} raw facts -> {len(validated)} validated")
            last_facts = all_facts
            print()
            continue

        log_id = user_input.upper()
        if log_id in logs_by_id:
            log = logs_by_id[log_id]
            print(f"Extracting facts from {log_id} ({log.get('author', 'unknown')})...")
            facts, raw_json = extract_facts(log["content"], client)
            last_facts = facts
            last_raw_json = raw_json
            display_facts(facts)
            print()
        else:
            print(f"  Unknown command or log ID: {user_input}")
            print("  Enter a log ID (e.g. LOG-001), /all, /validate, /json, /schema, or quit.")


if __name__ == "__main__":
    main()
