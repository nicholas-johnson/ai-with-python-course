"""
Exercise 01 — Chain Basics (solution)
Run:  python solution.py
"""

from __future__ import annotations

import os
import time
from typing import Literal

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

SAMPLE_REPORTS = [
    "Main drive output at 91% during station power draw. Cargo hold pressure stable.",
    "Spectroscopy on Cluster Theta-9 suggests nickel-iron rubble with trace platinum.",
    "Docking seal ring 3 integrity at 89% after patch — monitoring before undock.",
    "Berth 9-A assigned at L5-Prime. Fuel reserves sufficient with 8% margin.",
]

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


# ---------------------------------------------------------------------------
# Chains
# ---------------------------------------------------------------------------

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the CSS Horizon.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)

# Structured output: the model is constrained to the Classification schema.
chain = prompt | model.with_structured_output(Classification)

# Parser-based chains for comparison. The JSON parser relies on the prompt
# asking for JSON, so it gets its own instruction.
json_prompt = prompt + (
    "system",
    'Respond with ONLY a JSON object with keys "category", "summary", "priority".',
)
json_chain = json_prompt | model | JsonOutputParser()
raw_chain = prompt | model | StrOutputParser()


def classify_report(report: str) -> dict:
    """Classify a crew report. Returns {category, summary, priority}."""
    return chain.invoke({"report": report}).model_dump()


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  EXERCISE 01 — CHAIN BASICS")
    print("  Classify crew reports with an LCEL chain")
    print("=" * 60)

    print("\nSample reports to try:\n")
    for i, report in enumerate(SAMPLE_REPORTS, 1):
        print(f"  {i}. {report[:70]}...")

    print("\nCommands: /stream, /raw, /batch, /compare, quit\n")

    last_report = None

    while True:
        try:
            user_input = input("Report> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break

        if user_input == "/stream" and last_report:
            # Structured output arrives as one complete object, so stream the
            # JSON-parser chain instead: it yields the partial dict as it fills in.
            print()
            for partial in json_chain.stream({"report": last_report}):
                print(f"  {partial}")
            print()
            continue

        if user_input == "/raw" and last_report:
            raw = raw_chain.invoke({"report": last_report})
            print(f"\n  Raw output: {raw}\n")
            continue

        if user_input == "/batch":
            print("\n  Classifying 4 reports in parallel with chain.batch()...\n")
            inputs = [{"report": r} for r in SAMPLE_REPORTS]
            t0 = time.perf_counter()
            results = chain.batch(inputs)
            elapsed = time.perf_counter() - t0
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.category:<12} | {result.priority:<8} | {result.summary}")
            print(f"\n  Done in {elapsed:.1f}s (batch sends all requests concurrently)\n")
            continue

        if user_input == "/compare" and last_report:
            structured = chain.invoke({"report": last_report})
            parsed = json_chain.invoke({"report": last_report})
            raw = raw_chain.invoke({"report": last_report})
            print(f"\n  Structured output: {structured!r}")
            print(f"  JSON parser:       {parsed}")
            print(f"  String parser:     {raw}")
            print("\n  Same prompt, same model — swap the last step, change the output type.\n")
            continue

        last_report = user_input
        try:
            result = classify_report(user_input)
            print(f"\n  Category: {result.get('category', '?')}")
            print(f"  Summary:  {result.get('summary', '?')}")
            print(f"  Priority: {result.get('priority', '?')}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


if __name__ == "__main__":
    main()
