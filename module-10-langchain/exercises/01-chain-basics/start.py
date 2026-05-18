"""
Exercise 01 — Chain Basics (DSS Pathfinder)
Build an LCEL chain that classifies crew reports.

Run:  python start.py
Test: pytest test_start.py -v
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

# TODO: Import LangChain components
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
# from langchain_core.output_parsers import JsonOutputParser

MODEL = "gpt-4o-mini"

SAMPLE_REPORTS = [
    "Warp core operating at 94% efficiency. Minor fluctuation in plasma conduit 7-B.",
    "Long-range sensors detecting unusual spectral signature at bearing 047 mark 3.",
    "Crew member reported dizziness and nausea after EVA — possible radiation exposure.",
    "Course correction complete. New heading 127 mark 4, ETA Kepler-442 in 68 hours.",
]


# ---------------------------------------------------------------------------
# TODO: Build your chain
# ---------------------------------------------------------------------------

# 1. Create a ChatPromptTemplate with:
#    - system message: instruct the model to classify reports and return JSON
#    - human message: {report} placeholder

# 2. Build the LCEL chain: prompt | model | parser

# 3. Implement classify_report using chain.invoke()


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
        # if user_input == "/stream": ...
        # if user_input == "/raw": ...

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
