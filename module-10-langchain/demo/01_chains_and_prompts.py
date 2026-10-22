"""
Demo 1: Chains and Prompts — LangChain prompt templates, output parsers, and LCEL chains.
Run:  python module-10-langchain/demo/01_chains_and_prompts.py

DSS Pathfinder: classify and summarise crew reports using composable chain steps.

Part 1: Build the chain — prompt template, model, parser, pipe operator
Part 2: Structured output — a Pydantic schema instead of "respond with JSON"
Part 3: Swap the last step — structured output vs JsonOutputParser vs StrOutputParser
Part 4: Interactive — classify your own reports

Requires: OPENAI_API_KEY environment variable.
"""

import json
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

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

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
json_parser = JsonOutputParser()
str_parser = StrOutputParser()

json_chain = prompt | model | json_parser
str_chain = prompt | model | str_parser


class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


structured_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])
structured_chain = structured_prompt | model.with_structured_output(Classification)


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
    print(f"  → Raw: {response.text[:120]}...\n")

    print("  Step 3: Parser extracts structured data")
    parsed = json_parser.invoke(response)
    print(f"  → Parsed: {json.dumps(parsed, indent=2)}\n")

    print("  All three steps in one line with LCEL:")
    print("    chain = prompt | model | json_parser")
    result = json_chain.invoke({"report": report})
    print(f"  → {json.dumps(result, indent=2)}")

    pause()


# ---------------------------------------------------------------------------
# Part 2: Structured output
# ---------------------------------------------------------------------------

def demo_structured_output():
    print("=" * 60)
    print("PART 2: STRUCTURED OUTPUT")
    print("=" * 60)

    print("\n  Part 1's prompt had to *ask* for JSON and spell out the keys.")
    print("  Instead, describe the result as a Pydantic model:\n")
    print("    class Classification(BaseModel):")
    print('        category: Literal["navigation", "engineering", ...]')
    print("        summary: str")
    print('        priority: Literal["low", "medium", "high", "critical"]\n')
    print("    chain = prompt | model.with_structured_output(Classification)\n")

    report = SAMPLE_REPORTS[2]
    print(f"  Report: {report[:80]}...")
    result = structured_chain.invoke({"report": report})
    print(f"  → {result!r}")
    print(f"  → result.priority = {result.priority!r}  (attribute access, typed)\n")

    print("  The provider is constrained to the schema, so a bad value can't come back.")
    print("  Pydantic enforces the same rules in your own code:")
    try:
        Classification(category="cooking", summary="x", priority="low")
    except ValidationError as e:
        print(f"  → ValidationError: {e.errors()[0]['msg']}")

    pause()


# ---------------------------------------------------------------------------
# Part 3: Swap the last step
# ---------------------------------------------------------------------------

def demo_swap_parser():
    print("=" * 60)
    print("PART 3: SWAP THE LAST STEP")
    print("=" * 60)

    report = SAMPLE_REPORTS[1]
    print(f"\n  Report: {report[:80]}...\n")

    print("  with_structured_output → Pydantic object:")
    result = structured_chain.invoke({"report": report})
    print(f"  → type={type(result).__name__}: {result!r}\n")

    print("  JsonOutputParser → dict:")
    result = json_chain.invoke({"report": report})
    print(f"  → type={type(result).__name__}: {json.dumps(result, indent=2)}\n")

    print("  StrOutputParser → raw string:")
    result = str_chain.invoke({"report": report})
    print(f"  → type=str: {result}\n")

    print("  Same model — swap the last step, change the output type.")
    print("  One thing the JSON parser still does better: streaming partial results.")
    partials = list(json_chain.stream({"report": report}))
    for partial in partials[:: max(1, len(partials) // 6)] + partials[-1:]:
        print(f"    stream → {partial}")
    print(f"    ({len(partials)} partial dicts in total)")

    pause()


# ---------------------------------------------------------------------------
# Part 4: Interactive
# ---------------------------------------------------------------------------

def demo_interactive():
    print("=" * 60)
    print("PART 4: INTERACTIVE — CLASSIFY YOUR OWN REPORTS")
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
            result = structured_chain.invoke({"report": user_input})
            print(f"\n  Category: {result.category}")
            print(f"  Summary:  {result.summary}")
            print(f"  Priority: {result.priority}\n")
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Build the chain", demo_build_chain),
    "2": ("Structured output", demo_structured_output),
    "3": ("Swap the last step", demo_swap_parser),
    "4": ("Interactive",     demo_interactive),
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
    print("  model.with_structured_output(Schema) — typed results, no JSON prompting")
    print("  Swap any step without touching the others")
    print("  .invoke() runs it, .stream() streams it, .batch() parallelises it")
    print("=" * 60)


if __name__ == "__main__":
    main()
