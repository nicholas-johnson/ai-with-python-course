"""
Exercise 01 — Chain Basics (solution)
Run:  python solution.py
"""

from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL = "gpt-4o-mini"

SAMPLE_REPORTS = [
    "Warp core operating at 94% efficiency. Minor fluctuation in plasma conduit 7-B.",
    "Long-range sensors detecting unusual spectral signature at bearing 047 mark 3.",
    "Crew member reported dizziness and nausea after EVA — possible radiation exposure.",
    "Course correction complete. New heading 127 mark 4, ETA Kepler-442 in 68 hours.",
]

# ---------------------------------------------------------------------------
# Chain
# ---------------------------------------------------------------------------

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary of the report,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])

model = ChatOpenAI(model=MODEL, temperature=0)
parser = JsonOutputParser()

chain = prompt | model | parser
raw_chain = prompt | model | StrOutputParser()


def classify_report(report: str) -> dict:
    """Classify a crew report. Returns {category, summary, priority}."""
    return chain.invoke({"report": report})


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

    print("\nCommands: /stream, /raw, quit\n")

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
            print()
            for chunk in chain.stream({"report": last_report}):
                print(chunk, end="", flush=True)
            print("\n")
            continue

        if user_input == "/raw" and last_report:
            raw = raw_chain.invoke({"report": last_report})
            print(f"\n  Raw output: {raw}\n")
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
