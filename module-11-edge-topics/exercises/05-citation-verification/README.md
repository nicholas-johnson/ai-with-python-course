# Exercise 05 — Citation Verification

## Recap

### The problem: LLMs make things up

When an LLM generates an answer from retrieved passages, it sometimes adds "facts" that aren't in the source material. This is called **hallucination**. In casual chat it's annoying; in medical, legal, or engineering contexts it's dangerous.

### The solution: verify every claim

**Citation verification** is a post-processing step that:

1. **Extracts claims** — breaks the generated answer into individual factual statements.
2. **Checks each claim** — compares it against the source passages to see if any passage actually supports it.
3. **Flags unsupported claims** — gives you a report showing which claims are grounded and which were made up.

### How claim extraction works

You ask the LLM to decompose an answer into atomic facts:

```
Input answer: "The reactor operates at 3500K and requires daily
calibration by the engineering team."

Extracted claims:
- The reactor operates at 3500K
- The reactor requires daily calibration
- Calibration is done by the engineering team
```

Each claim can then be independently checked against the source passages.

### How verification works

For each claim, you ask the LLM: "Does this passage support this claim?" with a forced yes/no answer:

```
Does this passage support the following claim?
Answer exactly 'supported' or 'unsupported'.

Claim: The reactor operates at 3500K

Passage: Core thermal readings show steady operation at 3500 Kelvin
across all monitored intervals.
```

The LLM responds: `supported`

## What you build

Three functions in **`start.py`**:

| Function | What it does |
|---|---|
| `extract_claims(client, answer)` | Break an answer into a list of individual factual claims |
| `check_claim_support(client, claim, passage)` | Check if one passage supports one claim ("supported" or "unsupported") |
| `verify_answer(client, answer, passages)` | Full pipeline: extract all claims, check each against all passages |

## Data format

Input — an answer string and a list of source passages:

```python
answer = "The reactor operates at 3500K and uses dilithium crystals for containment."
passages = [
    "Core thermal readings show steady operation at 3500 Kelvin.",
    "Navigation systems use stellar cartography for route planning.",
]
```

Output — a list of verification results:

```python
[
    {
        "claim": "The reactor operates at 3500K",
        "supported": True,
        "supporting_passage": "Core thermal readings show steady operation at 3500 Kelvin.",
    },
    {
        "claim": "The reactor uses dilithium crystals for containment",
        "supported": False,
        "supporting_passage": None,
    },
]
```

## Step-by-step

### 1. Implement `extract_claims`

Prompt the LLM to split the answer into individual claims, one per line:

```python
def extract_claims(client: OpenAI, answer: str) -> list[str]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                "Extract each distinct factual claim from this text. "
                "Write one claim per line. Do not add numbering or bullets.\n\n"
                f"Text: {answer}"
            ),
        }],
        temperature=0,
    )
    lines = response.choices[0].message.content.strip().split("\n")
    return [line.strip() for line in lines if line.strip()]
```

### 2. Implement `check_claim_support`

For a single claim and passage pair, ask the LLM for a binary verdict:

```python
content = (
    "Does this passage support the following claim? "
    "Answer exactly 'supported' or 'unsupported'.\n\n"
    f"Claim: {claim}\n\n"
    f"Passage: {passage}"
)
```

> **Important:** Check the response carefully. The LLM might say "unsupported" or "not supported" — both mean the same thing. A safe check: if "supported" is in the response AND "unsupported" is NOT in the response, it's supported.

### 3. Implement `verify_answer`

For each extracted claim, loop through all passages looking for support. If any passage supports the claim, mark it as supported and record which passage:

```python
for claim in claims:
    supported = False
    supporting_passage = None
    for passage in passages:
        verdict = check_claim_support(client, claim, passage)
        if verdict == "supported":
            supported = True
            supporting_passage = passage
            break  # no need to check more passages
    results.append({...})
```

## Try it

```bash
cd module-11-edge-topics/exercises/05-citation-verification
python start.py
```

Try verifying answers that mix real facts with made-up ones: "The ship travels at warp 9 and has a crew of 50,000. The captain is named Kirk."

## Running Tests

```bash
pytest module-11-edge-topics/exercises/05-citation-verification/test_start.py -v
```

## Stretch Goals

- Add a "partial" support level (supported / partially supported / unsupported).
- Generate a revised answer that removes unsupported claims.
- Add source attribution (which passage supports which claim) as `[Source N]` tags.
