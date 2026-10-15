# Exercise 05 — Eval Compare

## Recap

You now have three kinds of number:

- Retrieval: recall, precision, MRR (Exercise 02)
- Judge: correctness, completeness, relevance (Exercise 03)
- Faithfulness: supported-claim ratio (Exercise 04)

A **scorecard** is those numbers for one pipeline config (`rag` vs `rag_rerank`). **Compare** ranks configs on one metric. A **gate** is a release floor: if recall drops below 0.6, the build fails even if someone liked the demo.

This exercise does **not** re-run RAG. It consumes already-aggregated dicts (see `data/config_runs.json`) so the tests stay deterministic and free.

### Overall score

Normalise everything to 0–1, then weight:

```
judge_norm = (avg_correctness + avg_completeness + avg_relevance) / 15
overall    = 0.35 * avg_recall + 0.35 * judge_norm + 0.30 * avg_faithfulness
```

Recall is the retrieval headline; the three judge scores share one third of the weight; faithfulness is the hallucination check. Precision and MRR stay on the card for inspection but do not enter `overall`.

## What you build

| Function | What it does |
|---|---|
| `overall_score(retrieval, judge, faithfulness)` | Weighted 0–1 score |
| `build_scorecard(name, retrieval, judge, faithfulness)` | Nested dict + `overall` |
| `metric_value(scorecard, metric)` | Look up `overall` or a nested key |
| `compare_configs(scorecards, metric)` | Winner + ranking (high to low) |
| `gate(scorecard, thresholds)` | Fail metrics strictly below a floor |

`build_scorecard` returns:

```python
{
    "config": "rag_rerank",
    "retrieval": {"avg_recall": 0.8, "avg_precision": 0.6, "avg_mrr": 0.85},
    "judge": {"avg_correctness": 4.1, "avg_completeness": 3.9, "avg_relevance": 4.4},
    "faithfulness": {"avg_faithfulness": 0.88},
    "overall": 0.83,
}
```

`gate` returns:

```python
{
    "passed": False,
    "failures": [{"metric": "avg_recall", "value": 0.4, "threshold": 0.6}],
}
```

Equal to the threshold **passes**. Empty `scorecards` → `winner` is `None`.

`metric_value` understands: `overall`, `avg_recall`, `avg_precision`, `avg_mrr`, `avg_correctness`, `avg_completeness`, `avg_relevance`, `avg_faithfulness`.

## Step-by-step

### 1. `overall_score`

Implement the formula. Constants `RECALL_WEIGHT`, `JUDGE_WEIGHT`, `FAITH_WEIGHT` are already in `start.py`.

### 2. `build_scorecard`

Put the inputs on the dict and set `"overall"`.

### 3. `metric_value`

`overall` is top-level. Retrieval / judge / faithfulness keys live one level down.

### 4. `compare_configs`

Sort by `metric_value` descending. First name is the winner.

### 5. `gate`

For each `thresholds` item, if `metric_value < floor`, append a failure. `passed` iff the list is empty.

## Try it

```bash
cd module-11-evals/exercises/05-eval-compare
python start.py
```

`rag` should lose and fail the gate; `rag_rerank` should win and pass.

## Running Tests

```bash
pytest module-11-evals/exercises/05-eval-compare/test_start.py -v
```

## Stretch Goals

- Make weights configurable so a medical domain can emphasise faithfulness.
- Gate on a *delta* vs last week's scorecard, not only an absolute floor.
- Plug this into a Module 12 capstone as a `/eval` endpoint that returns JSON.
