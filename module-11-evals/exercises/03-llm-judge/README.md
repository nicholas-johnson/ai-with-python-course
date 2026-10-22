# Exercise 03 — LLM-as-Judge

## Recap

### The problem: how do you know if your RAG system is good?

You can't improve what you can't measure. Traditional text metrics like BLEU and ROUGE count word overlap, but they're terrible at judging whether an answer is actually *correct* or *helpful*. "The reactor is at 3500K" and "Core temperature reads 3500 Kelvin" have low word overlap but mean the same thing.

### The solution: use an LLM as a judge

**LLM-as-judge** evaluation asks a strong model to read the question, the generated answer, and a reference answer, then score the quality on multiple dimensions:

- **Correctness** — Are the facts in the answer accurate?
- **Completeness** — Does it cover all the key points from the reference?
- **Relevance** — Does it actually address the question asked?

Each dimension gets a score from 1 (terrible) to 5 (perfect). You run this across a test set of question/answer/reference triples and compute averages.

### What the evaluation prompt looks like

```
Evaluate this answer against the reference answer.

Question: What causes warp core instability?

Candidate Answer: Warp core instability is caused by crystal degradation.

Reference Answer: Warp core instability is primarily caused by dilithium
crystal degradation, plasma injection asymmetry, and magnetic containment
fluctuations.

Score each dimension from 1 (worst) to 5 (best):
- Correctness: Are the facts accurate?
- Completeness: Does it cover all key points from the reference?
- Relevance: Does it directly address the question?
```

The scores come back through **structured outputs** (module 6): the judge's reply is constrained to a `JudgeScores` schema, so it might return `JudgeScores(correctness=5, completeness=2, relevance=5, explanation="Correct but only mentions one of three causes.")` -- never a missing score or a stray markdown fence.

### Why this matters

Once you have scores, you can compare different RAG configurations side-by-side: "Does adding re-ranking improve completeness? Does HyDE improve relevance?" Without evaluation, you're guessing. Exercise 05 turns those scores into a scorecard.

Pytest mocks the client — you do not need an API key to pass the tests.

## What you build

Three functions in **`start.py`**:

| Function | What it does |
|---|---|
| `llm_judge(client, question, answer, reference)` | Score one answer on correctness, completeness, relevance |
| `evaluate_dataset(client, test_cases)` | Run the judge across a full test set |
| `compute_summary(results)` | Calculate average scores per dimension |

## Data format

Each test case is a dict with three fields:

```python
test_cases = [
    {
        "question": "What causes warp core instability?",
        "answer": "Crystal degradation causes it.",
        "reference": "Dilithium crystal degradation, plasma injection asymmetry, and containment fluctuations.",
    },
    {
        "question": "Who leads the engineering team?",
        "answer": "Lt. Torres leads engineering.",
        "reference": "Chief Engineer Mira Chen leads engineering on Pathfinder.",
    },
]
```

`llm_judge` returns a dict of scores:

```python
{"correctness": 5, "completeness": 2, "relevance": 5, "explanation": "Only mentions one cause."}
```

`compute_summary` returns averages:

```python
{"avg_correctness": 4.2, "avg_completeness": 3.8, "avg_relevance": 4.5, "num_cases": 10}
```

## Step-by-step

### 1. Implement `llm_judge`

Define the score schema, build the evaluation prompt, and call `parse()` with `text_format=JudgeScores`:

```python
class JudgeScores(BaseModel):
    correctness: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    explanation: str

def llm_judge(client, question, answer, reference):
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=JudgeScores,
        input=[{
            "role": "user",
            "content": (
                f"Evaluate this answer against the reference answer.\n\n"
                f"Question: {question}\n\n"
                f"Candidate Answer: {answer}\n\n"
                f"Reference Answer: {reference}\n\n"
                f"Score each dimension from 1 (worst) to 5 (best):\n"
                f"- Correctness: Are the facts accurate?\n"
                f"- Completeness: Does it cover all key points from the reference?\n"
                f"- Relevance: Does it directly address the question?"
            ),
        }],
        temperature=0,
    )
    return response.output_parsed.model_dump()
```

> **Important:** If the model refuses, `response.output_parsed` is `None`. Return default scores of 1 with that explanation rather than crashing. The `ge=1, le=5` bounds are part of the schema, so an out-of-range score can't come back.

### 2. Implement `evaluate_dataset`

Loop through test cases, call `llm_judge` for each, and merge the scores into the original case dict:

```python
def evaluate_dataset(client, test_cases):
    results = []
    for case in test_cases:
        scores = llm_judge(client, case["question"], case["answer"], case["reference"])
        results.append({**case, **scores})
    return results
```

### 3. Implement `compute_summary`

Average each dimension across all results:

```python
def compute_summary(results):
    n = len(results)
    if n == 0:
        return {"avg_correctness": 0.0, "avg_completeness": 0.0, "avg_relevance": 0.0, "num_cases": 0}
    return {
        "avg_correctness": sum(r["correctness"] for r in results) / n,
        "avg_completeness": sum(r["completeness"] for r in results) / n,
        "avg_relevance": sum(r["relevance"] for r in results) / n,
        "num_cases": n,
    }
```

## Try it

```bash
cd module-11-evals/exercises/03-llm-judge
python start.py
```

Uses a mocked client so it runs without an API key.

## Running Tests

```bash
pytest module-11-evals/exercises/03-llm-judge/test_start.py -v
```

## Stretch Goals

- Exercise 04 adds a **faithfulness** check against retrieved context (not the reference).
- Run the judge multiple times and average scores for more stability.
- Exercise 05 compares two RAG configurations on the same test set.
