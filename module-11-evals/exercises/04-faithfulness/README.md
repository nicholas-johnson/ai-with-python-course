# Exercise 04 — Faithfulness

## Recap

The judge in [exercise 03](../03-llm-judge/) scores an answer against a **reference**. That leaves a gap. An answer can agree with the reference and still contain something the pipeline never retrieved — the model knew it from pre-training, or simply made it up. Either way you have no evidence for it, and no way to show a user where it came from.

**Faithfulness** asks a different question: is every claim in the answer supported by the context you actually retrieved? The reference answer plays no part.

1. Split the answer into atomic claims.
2. For each claim, ask the model whether the context supports it.
3. Divide: `faithfulness = supported_claims / total_claims`.

```
Answer:  "The warp core is at 94% efficiency. Core temperature is 9000K."
Context: "Warp core operating at 94% efficiency. Minor fluctuation in plasma conduit 7-B."

Claim 1 — 94% efficiency  → supported
Claim 2 — 9000K           → unsupported
faithfulness = 1/2 = 0.5
```

This is the generation-side cousin of citation verification in Module 13. The difference is what you get back: a ratio rather than a list of citations, which is what lets it sit on a scorecard next to recall and the judge averages.

One thing faithfulness does *not* tell you is whether the source was right. An answer that faithfully repeats a stale log scores 1.0. Grounding and correctness are separate properties, which is why [exercise 05](../05-eval-compare/) keeps both on the card.

### The dataset

The same five questions again, answered by both configs, each paired with the context that config actually retrieved. The averages feed the scorecard in exercise 05.

Pytest mocks the client, and so does `start.py`, so no API key is needed.

## What you build

| Function | What it does |
|---|---|
| `extract_claims(client, answer)` | Split an answer into one factual claim per line |
| `check_support(client, claim, context)` | Return `"supported"` or `"unsupported"` |
| `score_faithfulness(client, answer, context)` | Per-claim rows plus the ratio |

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

An answer with zero claims scores `1.0`. There is nothing in it to hallucinate.

## Step-by-step

### 1. Implement `extract_claims`

Prompt the model to list each factual claim from the answer on its own line, with no numbering or bullets, then split the reply on newlines and drop any blank lines. Asking for one claim per line keeps the parsing trivial; asking for JSON here would work too but costs more tokens for no benefit.

### 2. Implement `check_support`

Prompt the model with the claim and the context and ask for exactly one of two words back. Lowercase the reply before you inspect it.

Check for `"unsupported"` **before** you check for `"supported"`, because the second word is a substring of the first — a naive `"supported" in verdict` matches both and silently marks every hallucination as grounded. Treat anything you do not recognise as unsupported, so an unparseable reply fails safe rather than inflating the score.

### 3. Implement `score_faithfulness`

Call `extract_claims`, then `check_support` on each claim against the **full** context string. Build the per-claim rows, count the supported ones, and divide. Remember the zero-claim case returns `1.0` rather than dividing by zero.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/04-faithfulness
python start.py

# Option B - uv (no activation needed):
cd module-11-evals/exercises/04-faithfulness
uv run python start.py
```

This scores both configs and prints every claim with its verdict. Two cases are worth reading closely:

- On the crew radiation question, plain `rag` retrieved nothing relevant and the generator filled the gap with invented detail. Faithfulness drops to 0.0, and it is the only metric in this module that catches it as a *grounding* failure rather than a vague quality dip.
- On the TRAPPIST water question, `rag_rerank` says the radar probe "has confirmed" the subsurface water. The log says a probe is being deployed *for* confirmation. The claim is plausible, close to the reference, and would likely slip past the judge — but it is not in the context, so faithfulness marks it.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/04-faithfulness
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-11-evals/exercises/04-faithfulness
uv run --extra dev pytest test_start.py -v
```

The tests check:

- `extract_claims` returns a list of strings and filters out blank lines
- `check_support` returns only the two permitted labels
- `score_faithfulness` computes the ratio, counts supported claims, and keeps the claim text
- An answer with no claims scores `1.0`
- No real OpenAI calls — every test uses a mocked client

## Stretch goals

- Check each claim against a *list* of passages instead of one joined string, and record which passage supported it. That turns the score into citation verification.
- Take several verdicts per claim and use the majority, so a borderline claim does not flip between runs.
- Add a "partially supported" label and decide how it should count. Half a point is the obvious answer; think about whether it is the right one for a safety-critical domain.
