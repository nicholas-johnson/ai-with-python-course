"""
Exercise 05 — Citation Verification

Extract claims from an LLM-generated answer and verify
each claim is supported by the retrieved passages.
"""

from openai import OpenAI


def extract_claims(client: OpenAI, answer: str) -> list[str]:
    """
    Extract individual factual claims from an answer.

    Args:
        client: OpenAI client.
        answer: The LLM-generated answer text.

    Returns:
        A list of individual claim strings.

    TODO:
    - Prompt gpt-4o-mini to extract each factual claim as a separate line
    - Parse the response into a list of claims
    - Filter out empty lines
    """
    # TODO: implement claim extraction
    pass


def check_claim_support(
    client: OpenAI,
    claim: str,
    passage: str,
) -> str:
    """
    Check whether a passage supports a claim.

    Args:
        client: OpenAI client.
        claim: A single factual claim.
        passage: A source passage.

    Returns:
        One of: "supported", "unsupported"

    TODO:
    - Prompt gpt-4o-mini to determine if the passage supports the claim
    - Ask for exactly "supported" or "unsupported"
    - Return the verdict
    """
    # TODO: implement claim checking
    pass


def verify_answer(
    client: OpenAI,
    answer: str,
    passages: list[str],
) -> list[dict]:
    """
    Verify all claims in an answer against the source passages.

    Returns a list of dicts, one per claim:
    {
        "claim": str,
        "supported": bool,
        "supporting_passage": str | None,
    }

    TODO:
    - Extract claims from the answer
    - For each claim, check it against each passage
    - A claim is supported if ANY passage supports it
    - Return the verification results
    """
    # TODO: implement full verification pipeline
    pass
