"""Part 4: Check each claim in an answer against the source passages."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def demo_citation_verification():
    print("=" * 60)
    print("PART 4: CITATION VERIFICATION")
    print("=" * 60)
    print()

    client = OpenAI()
    passages = [
        "The reactor core operates at 5000 degrees Kelvin under normal conditions.",
        "The crew complement is 42 personnel.",
        "Hull integrity on deck 5 is at 94%.",
    ]
    answer = (
        "The reactor operates at 5000K. The ship has a crew of 42 people. "
        "The shields are at maximum power. Hull integrity on deck 5 is 94%."
    )

    print("Generated answer:")
    print(f"  '{answer}'\n")
    print("Source passages:")
    for i, passage in enumerate(passages, 1):
        print(f"  [{i}] {passage}")
    print()

    extract_resp = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[{
            "role": "user",
            "content": f"Extract each factual claim as a separate line:\n\n{answer}",
        }],
    )
    claims = [line.strip() for line in extract_resp.output_text.split("\n") if line.strip()]

    for claim in claims:
        supported = False
        source = None
        for passage in passages:
            resp = client.responses.create(
                model=MODEL,
                reasoning={"effort": "none"},
                input=[{
                    "role": "user",
                    "content": (
                        "Does this passage support this claim? "
                        "Answer 'supported' or 'unsupported'.\n\n"
                        f"Claim: {claim}\nPassage: {passage}"
                    ),
                }],
            )
            verdict = resp.output_text.strip().lower()
            if "supported" in verdict and "unsupported" not in verdict:
                supported = True
                source = passage[:40]
                break

        mark = "ok" if supported else "!!"
        src = f" ← '{source}...'" if source else ""
        print(f"  [{mark}] {claim}{src}")
    print()
