# Exercise 08 — LLM Eval (LLM-as-Judge)

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

Respond with JSON only: {"correctness": N, "completeness": N, "relevance": N, "explanation": "..."}
```

The judge might respond: `{"correctness": 5, "completeness": 2, "relevance": 5, "explanation": "Correct but only mentions one of three causes."}`

### Why this matters

Once you have scores, you can compare different RAG configurations side-by-side: "Does adding re-ranking improve completeness? Does HyDE improve relevance?" Without evaluation, you're guessing.

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
        "reference": "Lieutenant B'Elanna Torres is the chief engineer.",
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

Build the evaluation prompt and ask for JSON output:

```python
def llm_judge(client, question, answer, reference):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Evaluate this answer against the reference answer.\n\n"
                f"Question: {question}\n\n"
                f"Candidate Answer: {answer}\n\n"
                f"Reference Answer: {reference}\n\n"
                f"Score each dimension from 1 (worst) to 5 (best):\n"
                f"- Correctness: Are the facts accurate?\n"
                f"- Completeness: Does it cover all key points from the reference?\n"
                f"- Relevance: Does it directly address the question?\n\n"
                f'Respond with JSON only: {{"correctness": N, "completeness": N, '
                f'"relevance": N, "explanation": "..."}}'
            ),
        }],
        temperature=0,
    )
    text = response.choices[0].message.content.strip()
    # Parse JSON from the response...
```

> **Important:** The model sometimes wraps JSON in markdown code fences. Strip ` ```json ` and ` ``` ` if present before calling `json.loads()`. If parsing fails, return default scores of 1 with an error explanation rather than crashing.

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
cd module-11-edge-topics/exercises/08-llm-eval
python start.py
```

## Running Tests

```bash
pytest module-11-edge-topics/exercises/08-llm-eval/test_start.py -v
```

## Stretch Goals

- Add a "faithfulness" dimension (is the answer grounded in context, not hallucinated?).
- Run the judge multiple times and average scores for more stability.
- Compare two different RAG configurations side-by-side on the same test set.
