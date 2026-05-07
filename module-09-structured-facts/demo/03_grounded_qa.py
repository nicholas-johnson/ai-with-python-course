"""Demo 03 — Grounded question-answering with citations.

Combines knowledge-graph lookups with source-document references to
answer questions with verifiable citations and confidence scores.
"""

from __future__ import annotations

from dataclasses import dataclass


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

    def format(self) -> str:
        lines = [
            f"Q: {self.question}",
            f"A: {self.answer}  (confidence: {self.confidence:.0%})",
            "Sources:",
        ]
        for i, c in enumerate(self.citations, 1):
            lines.append(f"  [{i}] {c.source_id} (relevance {c.relevance:.0%}): \"{c.text}\"")
        return "\n".join(lines)


MOCK_ANSWERS = [
    GroundedAnswer(
        question="Who repaired the port thruster array?",
        answer="Chief Engineer Vasquez repaired the port thruster array during the third watch.",
        citations=[
            Citation("ship_log_2287_03", "Chief Engineer Vasquez repaired the port thruster array during the third watch.", 0.98),
        ],
        confidence=0.96,
    ),
    GroundedAnswer(
        question="Is cargo bay 2 safe to enter?",
        answer="No — Dr. Okafor reported elevated radiation levels and recommended sealing the section.",
        citations=[
            Citation("ship_log_2287_03", "Dr. Okafor reported elevated radiation levels in cargo bay 2 and recommended sealing the section.", 0.95),
            Citation("safety_protocol_7B", "Sections with radiation above 50 mSv/hr must be sealed until cleared by medical.", 0.82),
        ],
        confidence=0.91,
    ),
]


def main() -> None:
    print("=== Grounded QA Demo ===\n")
    for answer in MOCK_ANSWERS:
        print(answer.format())
        print()


if __name__ == "__main__":
    main()
