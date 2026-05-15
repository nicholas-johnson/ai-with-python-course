"""
Demo 1: Chains and Prompts — LangChain prompt templates, output parsers, and LCEL chains.
Run:  python module-10-langchain/demo/01_chains_and_prompts.py

DSS Pathfinder: classify and summarise crew reports using composable chain steps.

Part 1: Build the chain — prompt template, model, parser, pipe operator
Part 2: Swap the parser — JsonOutputParser vs StrOutputParser
Part 3: Interactive — classify your own reports

Requires: OPENAI_API_KEY environment variable.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL = "gpt-4o-mini"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS = json.loads((PROJECT_ROOT / "data" / "ship_logs.json").read_text())

SAMPLE_REPORTS = [log["content"] for log in LOGS[:5]]


# ---------------------------------------------------------------------------
# Chain components
# ---------------------------------------------------------------------------

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])

model = ChatOpenAI(model=MODEL, temperature=0)
json_parser = JsonOutputParser()
str_parser = StrOutputParser()

json_chain = prompt | model | json_parser
str_chain = prompt | model | str_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pause():
    try:
        input("\n  [Press Enter to continue...]\n")
    except (EOFError, KeyboardInterrupt):
        print()


# ---------------------------------------------------------------------------
# Part 1: Build the chain
# ---------------------------------------------------------------------------

def demo_build_chain():
    print("=" * 60)
    print("PART 1: BUILD THE CHAIN")
    print("=" * 60)

    report = SAMPLE_REPORTS[0]
    print(f"\n  Report: {report[:80]}...\n")

    print("  Step 1: Prompt template renders the report into messages")
    messages = prompt.invoke({"report": report})
    print(f"  → {len(messages.messages)} messages (system + human)\n")

    print("  Step 2: Model generates a response")
    response = model.invoke(messages)
    print(f"  → Raw: {response.content[:120]}...\n")

    print("  Step 3: Parser extracts structured data")
    parsed = json_parser.invoke(response)
    print(f"  → Parsed: {json.dumps(parsed, indent=2)}\n")

    print("  All three steps in one line with LCEL:")
    print("    chain = prompt | model | json_parser")
    result = json_chain.invoke({"report": report})
    print(f"  → {json.dumps(result, indent=2)}")

    pause()


# ---------------------------------------------------------------------------
# Part 2: Swap the parser
# ---------------------------------------------------------------------------

def demo_swap_parser():
    print("=" * 60)
    print("PART 2: SWAP THE PARSER")
    print("=" * 60)

    report = SAMPLE_REPORTS[1]
    print(f"\n  Report: {report[:80]}...\n")

    print("  JsonOutputParser → dict:")
    result = json_chain.invoke({"report": report})
    print(f"  → type={type(result).__name__}: {json.dumps(result, indent=2)}\n")

    print("  StrOutputParser → raw string:")
    result = str_chain.invoke({"report": report})
    print(f"  → type={type(result).__name__}: {result}\n")

    print("  Same prompt, same model — different parser, different output type.")
    print("  Swap components without changing anything else.")

    pause()


# ---------------------------------------------------------------------------
# Part 3: Interactive
# ---------------------------------------------------------------------------

def demo_interactive():
    print("=" * 60)
    print("PART 3: INTERACTIVE — CLASSIFY YOUR OWN REPORTS")
    print("=" * 60)

    print("\nSample reports:\n")
    for i, report in enumerate(SAMPLE_REPORTS, 1):
        print(f"  {i}. {report[:70]}...")

    print("\nType a report to classify. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("Report> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break

        try:
            result = json_chain.invoke({"report": user_input})
            print(f"\n  Category: {result.get('category', '?')}")
            print(f"  Summary:  {result.get('summary', '?')}")
            print(f"  Priority: {result.get('priority', '?')}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Build the chain", demo_build_chain),
    "2": ("Swap the parser", demo_swap_parser),
    "3": ("Interactive",     demo_interactive),
}


def main():
    print("\n" + "=" * 60)
    print("  DEMO 1 — CHAINS AND PROMPTS")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("RECAP")
    print("=" * 60)
    print()
    print("  prompt | model | parser  — that's the whole chain")
    print("  Swap any step without touching the others")
    print("  .invoke() runs it, .stream() streams it, .batch() parallelises it")
    print("=" * 60)


if __name__ == "__main__":
    main()
