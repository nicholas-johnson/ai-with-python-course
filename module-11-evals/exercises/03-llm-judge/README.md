# Exercise 03 — LLM-as-Judge

## Recap

Exercise 01 ended on a problem. The agent answered "The captain is Commander Elara Voss" where the reference said "Commander Elara Voss is the captain", and exact matching called it a failure. Word-overlap metrics like BLEU and ROUGE have the same blind spot: "The reactor is at 3500K" and "Core temperature reads 3500 Kelvin" share almost no words and mean the same thing.

An **LLM-as-judge** reads the question, the candidate answer, and a reference answer, then scores the answer on dimensions you define:

- **Correctness** — are the facts accurate?
- **Completeness** — does it cover the key points in the reference?
- **Relevance** — does it address the question that was asked?

Each dimension is scored from 1 to 5. Run it across a test set and average the results, and you have a number that survives paraphrase.

The scores come back through **structured outputs** (Module 6). Constrain the reply to a `JudgeScores` schema and the judge returns something like `JudgeScores(correctness=5, completeness=2, relevance=5, explanation="Correct but only mentions one of three causes.")` — never a missing score, an out-of-range score, or a stray markdown fence to strip.

Judge bias is real, so treat these scores as *relative* rather than absolute. "Config A beats config B on completeness" is a far safer claim than "this answer is objectively a 4".

### The dataset

The same five ship-log questions from [exercise 02](../02-retrieval-metrics/), answered by both pipeline configs. Because `rag` and `rag_rerank` retrieved different documents, they produced different answers to identical questions — which is exactly what you want to measure. The averages you produce here feed the scorecard in [exercise 05](../05-eval-compare/).

### What the evaluation prompt looks like

```
Evaluate this answer against the reference answer.

Question: What is the current warp core efficiency?

Candidate Answer: The warp core is operating at 94% efficiency, with a minor
fluctuation in plasma conduit 7-B.

Reference Answer: The warp core is currently at 97% efficiency. It was running
at 94% with a minor fluctuation in plasma conduit 7-B until the repair was
completed during EVA downtime.

Score each dimension from 1 (worst) to 5 (best):
- Correctness: Are the facts accurate?
- Completeness: Does it cover all key points from the reference?
- Relevance: Does it directly address the question?
```

Pytest mocks the client, and so does `start.py`, so you need no API key for either.

## What you build

Three functions in **`start.py`**. `load_cases` and `make_canned_judge` are already written.

| Function | What it does |
|---|---|
| `llm_judge(client, question, answer, reference)` | Score one answer on correctness, completeness and relevance |
| `evaluate_dataset(client, test_cases)` | Run the judge across a full test set |
| `compute_summary(results)` | Average each dimension across the results |

Each test case carries a question, the answer the pipeline gave, and the reference:

```python
{
    "id": "warp-efficiency",
    "question": "What is the current warp core efficiency?",
    "answer": "The warp core is operating at 94% efficiency, ...",
    "reference": "The warp core is currently at 97% efficiency. ...",
}
```

`llm_judge` returns the scores as a dict:

```python
{"correctness": 3, "completeness": 2, "relevance": 5, "explanation": "The 94% figure is stale."}
```

`compute_summary` returns the averages:

```python
{"avg_correctness": 3.8, "avg_completeness": 2.4, "avg_relevance": 4.4, "num_cases": 5}
```

## Step-by-step

### 1. Implement `llm_judge`

First define the schema above the function. Each dimension is an `int` bounded with `Field(ge=1, le=5)`, plus an `explanation: str` so a human reading the results later knows why a score was given:

```python
class JudgeScores(BaseModel):
    correctness: int = Field(ge=1, le=5)
    ...
```

Then build the evaluation prompt from the question, candidate answer and reference, and send it with `client.responses.parse(..., text_format=JudgeScores, temperature=0)`. Temperature 0 matters here: a judge that returns a different score each run is not a measurement.

Return `response.output_parsed.model_dump()`. If the model refused, `output_parsed` is `None` — return scores of 1 with an explanation saying so rather than crashing, because one refusal should not take down a whole suite. You do not need to validate the range yourself; the `ge` and `le` bounds are part of the schema the model is constrained to.

### 2. Implement `evaluate_dataset`

Loop over the test cases, call `llm_judge` for each, and merge the scores into the original case dict so the question and answer travel with their scores. Returning `{**case, **scores}` keeps both halves together.

### 3. Implement `compute_summary`

Average `correctness`, `completeness` and `relevance` across the results and report `num_cases`. Return zeros for an empty list rather than dividing by zero.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/03-llm-judge
python start.py

# Option B - uv (no activation needed):
cd module-11-evals/exercises/03-llm-judge
uv run python start.py
```

This judges both configs and prints per-case scores with the judge's reasoning, then the averages. `rag_rerank` wins on every dimension — except on the void navigation question, where it scores worse than plain `rag`. That is the retrieval miss you saw in exercise 02 showing up one layer down: the generator cannot be accurate about a document it was never given.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/03-llm-judge
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-11-evals/exercises/03-llm-judge
uv run --extra dev pytest test_start.py -v
```

The tests check:

- `llm_judge` returns all three scores plus an explanation, as integers
- `llm_judge` calls the API once per case and falls back to scores of 1 on a refusal
- `evaluate_dataset` keeps the original case data alongside the scores
- `evaluate_dataset` handles an empty dataset
- `compute_summary` averages each dimension and returns floats
- No real OpenAI calls — every test uses a mocked client

## Stretch goals

- Run the judge several times per case and average, so a single odd score does not move the headline number.
- Add a fourth dimension such as conciseness, and see whether it correlates with the other three or tells you something new.
- Swap the judge model for a smaller one and compare the two sets of scores. If the ranking of configs survives, the cheaper judge is good enough for routine runs.
