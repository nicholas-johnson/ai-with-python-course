# Exercise 04 — Faithfulness

## Recap

An LLM-as-judge (Exercise 03) scores an answer against a **reference**. That misses a different failure: the answer agrees with the reference but **is not in the retrieved context** — or worse, the model invents a temperature that no log ever recorded.

**Faithfulness** asks: is every claim in the answer supported by the context you actually retrieved?

1. Split the answer into atomic claims.
2. For each claim, ask a model whether the context supports it (`supported` / `unsupported`).
3. `faithfulness = supported_claims / total_claims`.

```
Answer:  "The warp core is at 94% efficiency. Core temperature is 9000K."
Context: "Warp core operating at 94% efficiency. Plasma conduit 7-B fluctuation."

Claim 1 — 94% efficiency  → supported
Claim 2 — 9000K           → unsupported
faithfulness = 1/2 = 0.5
```

This is the generation-side cousin of citation verification (Module 13). Here you score a **ratio**, not a list of citations, so it can sit on a scorecard next to recall and judge averages.

Pytest mocks the client. No API key required to pass.

## What you build

| Function | What it does |
|---|---|
| `extract_claims(client, answer)` | One factual claim per line |
| `check_support(client, claim, context)` | `"supported"` or `"unsupported"` |
| `score_faithfulness(client, answer, context)` | Per-claim rows + ratio |

`score_faithfulness` returns:

```python
{
    "claims": [
        {"claim": "The warp core is at 94% efficiency.", "supported": True},
        {"claim": "Core temperature is 9000K.", "supported": False},
    ],
    "num_claims": 2,
    "num_supported": 1,
    "faithfulness": 0.5,
}
```

If there are **zero** claims, return `faithfulness` of `1.0` (nothing to hallucinate).

## Step-by-step

### 1. `extract_claims`

Prompt the model (`MODEL`) to list each claim on its own line, no bullets. Split on `\n` and drop blanks.

### 2. `check_support`

Prompt for exactly `supported` or `unsupported`. Lowercase the reply. If it contains `unsupported`, treat it as unsupported (the word "supported" sits inside "unsupported"). Anything else → `unsupported`.

### 3. `score_faithfulness`

`extract_claims`, then `check_support` each claim against the **full** context (one string, not a list of passages). Count, divide, return the dict.

## Try it

```bash
cd module-11-evals/exercises/04-faithfulness
python start.py
```

Runs three cases from `data/grounding_cases.json` with a mocked client.

## Running Tests

```bash
pytest module-11-evals/exercises/04-faithfulness/test_start.py -v
```

## Stretch Goals

- Check each claim against a *list* of passages and record which passage supported it (citation verification).
- Average several judge votes per claim to reduce flip-flops.
- Add a "partially supported" label and decide how it counts in the ratio.
