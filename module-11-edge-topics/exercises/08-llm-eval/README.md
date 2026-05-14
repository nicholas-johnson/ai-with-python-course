# Exercise 08 — LLM Eval (LLM-as-Judge)

## Recap

You cannot improve what you cannot measure. **LLM-as-judge** evaluation uses a strong model to score answers on dimensions like correctness, completeness, and relevance. This replaces surface-level metrics (BLEU, ROUGE) with semantic evaluation that understands meaning.

## Your Task

1. Implement `llm_judge(client, question, answer, reference)` — score an answer against a reference.
2. Implement `evaluate_dataset(client, test_cases)` — run evaluation across a test set.
3. Implement `compute_summary(results)` — aggregate scores into summary statistics.

## Steps

1. Open `start.py` and review the function signatures.
2. Implement `llm_judge`: prompt the LLM to score correctness, completeness, and relevance (1-5 each).
3. Implement `evaluate_dataset`: run the judge on each test case and collect results.
4. Implement `compute_summary`: calculate average scores per dimension.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/08-llm-eval/test_start.py -v
```

## Stretch Goals

- Add a "faithfulness" dimension (is the answer grounded in context?).
- Run the judge multiple times and average for more stable scores.
- Compare two different RAG configurations side-by-side.
