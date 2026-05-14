"""
Exercise 05 — Citation Verification (Solution)

Extract claims from an LLM-generated answer and verify
each claim is supported by the retrieved passages.
"""

from openai import OpenAI


def extract_claims(client: OpenAI, answer: str) -> list[str]:
    """
    Extract individual factual claims from an answer.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Extract each distinct factual claim from this text. "
                f"Write one claim per line. Do not add numbering or bullets.\n\n"
                f"Text: {answer}"
            ),
        }],
        temperature=0,
    )
    lines = response.choices[0].message.content.strip().split("\n")
    return [line.strip() for line in lines if line.strip()]


def check_claim_support(
    client: OpenAI,
    claim: str,
    passage: str,
) -> str:
    """
    Check whether a passage supports a claim.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Does this passage support the following claim? "
                f"Answer exactly 'supported' or 'unsupported'.\n\n"
                f"Claim: {claim}\n\n"
                f"Passage: {passage}"
            ),
        }],
        temperature=0,
    )
    verdict = response.choices[0].message.content.strip().lower()
    return "supported" if "supported" in verdict and "unsupported" not in verdict else "unsupported"


def verify_answer(
    client: OpenAI,
    answer: str,
    passages: list[str],
) -> list[dict]:
    """
    Verify all claims in an answer against the source passages.
    """
    claims = extract_claims(client, answer)
    results = []

    for claim in claims:
        supported = False
        supporting_passage = None

        for passage in passages:
            verdict = check_claim_support(client, claim, passage)
            if verdict == "supported":
                supported = True
                supporting_passage = passage
                break

        results.append({
            "claim": claim,
            "supported": supported,
            "supporting_passage": supporting_passage,
        })

    return results
