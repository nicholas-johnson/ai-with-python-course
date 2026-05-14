# Exercise 05 — Citation Verification

## Recap

LLMs can generate plausible claims not supported by the retrieved passages. **Citation verification** extracts claims from the generated answer, checks each one against the evidence passages, and flags unsupported claims. This is essential for high-stakes domains.

## Your Task

1. Implement `extract_claims(client, answer)` — break an answer into individual factual claims.
2. Implement `check_claim_support(client, claim, passage)` — verify if a passage supports a claim.
3. Implement `verify_answer(client, answer, passages)` — full verification pipeline.

## Steps

1. Open `start.py` and read through the function signatures.
2. Implement `extract_claims`: use the LLM to decompose the answer into individual claims.
3. Implement `check_claim_support`: use the LLM to judge whether a passage supports a claim.
4. Implement `verify_answer`: extract claims, check each against all passages, return a report.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/05-citation-verification/test_start.py -v
```

## Stretch Goals

- Add a "partial" support level (supported / partially supported / unsupported).
- Generate a revised answer that removes unsupported claims.
- Add source attribution (which passage supports which claim).
