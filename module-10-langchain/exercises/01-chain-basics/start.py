"""
Exercise 01 — Chain Basics (CSS Horizon)
Build an LCEL chain that classifies crew reports.

Run:  python start.py
Test: pytest test_start.py -v
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# TODO: Import LangChain components
# from typing import Literal
# from pydantic import BaseModel, Field
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
# from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

SAMPLE_REPORTS = [
    "Main drive output at 91% during station power draw. Cargo hold pressure stable.",
    "Spectroscopy on Cluster Theta-9 suggests nickel-iron rubble with trace platinum.",
    "Docking seal ring 3 integrity at 89% after patch — monitoring before undock.",
    "Berth 9-A assigned at L5-Prime. Fuel reserves sufficient with 8% margin.",
]


# ---------------------------------------------------------------------------
# TODO: Build your chain
# ---------------------------------------------------------------------------

# 1. Define a Pydantic model `Classification` with:
#    - category: Literal["navigation", "engineering", "science", "medical", "operations"]
#    - summary: str
#    - priority: Literal["low", "medium", "high", "critical"]

# 2. Create a ChatPromptTemplate with:
#    - system message: instruct the model to classify the report
#    - human message: {report} placeholder

# 3. Build the LCEL chain: prompt | model.with_structured_output(Classification)

# 4. Implement classify_report using chain.invoke() — it returns a Classification;
#    return it as a dict with .model_dump()


def classify_report(report: str) -> dict:
    """Classify a crew report. Returns {category, summary, priority}."""
    raise NotImplementedError("TODO: implement using your LCEL chain")


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

    print("\nType a report to classify, or 'quit' to exit.\n")

    last_report = None

    while True:
        try:
            user_input = input("Report> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break

        # TODO: handle /stream and /raw commands
        # if user_input == "/stream": ...  stream a JsonOutputParser chain (partial dicts)
        # if user_input == "/raw": ...     prompt | model | StrOutputParser()

        # TODO: handle /batch — use chain.batch() to classify all SAMPLE_REPORTS
        #   in parallel; wrap in time.perf_counter() to show wall-clock time
        # if user_input == "/batch": ...

        # TODO: handle /compare — invoke the structured-output chain, a
        #   JsonOutputParser chain, and a StrOutputParser chain on the last
        #   report to show composability
        # if user_input == "/compare" and last_report: ...

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
