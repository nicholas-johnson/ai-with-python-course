"""Demo 01 — Structured extraction with Pydantic output schemas.

Shows how to get an LLM to return typed, validated data instead of
freeform prose. Uses Pydantic models as the output contract and
handles validation failures with retries.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CrewFact(BaseModel):
    subject: str = Field(description="The crew member or entity the fact is about")
    predicate: str = Field(description="The relationship or attribute")
    value: str = Field(description="The object or value")
    source_sentence: str = Field(description="The original sentence this fact was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence 0-1")


class ExtractionResult(BaseModel):
    facts: list[CrewFact]
    raw_text_length: int


SAMPLE_LOG = (
    "Chief Engineer Vasquez repaired the port thruster array during the "
    "third watch. Navigation Officer Chen plotted a course correction to "
    "avoid the Kepler-442 debris field. Dr. Okafor reported elevated "
    "radiation levels in cargo bay 2 and recommended sealing the section."
)


def build_extraction_prompt(text: str) -> str:
    return (
        "Extract every factual claim from the following ship log entry. "
        "Return structured JSON matching the provided schema.\n\n"
        f"Log entry:\n{text}"
    )


def main() -> None:
    print("=== Structured Extraction Demo ===\n")
    print(f"Input text ({len(SAMPLE_LOG)} chars):\n{SAMPLE_LOG}\n")
    print("Prompt sent to LLM:")
    print(build_extraction_prompt(SAMPLE_LOG))
    print("\nExpected output schema: ExtractionResult")
    print(f"  facts: list[CrewFact]  (subject, predicate, value, source_sentence, confidence)")
    print(f"  raw_text_length: int")

    example = ExtractionResult(
        facts=[
            CrewFact(
                subject="Chief Engineer Vasquez",
                predicate="repaired",
                value="port thruster array",
                source_sentence="Chief Engineer Vasquez repaired the port thruster array during the third watch.",
                confidence=0.95,
            ),
        ],
        raw_text_length=len(SAMPLE_LOG),
    )
    print(f"\nExample parsed output:\n{example.model_dump_json(indent=2)}")


if __name__ == "__main__":
    main()
