# Exercise 15 — Hugging Face Run (CPU)

## Recap

Thousands of pre-trained models live on the Hugging Face Hub. The demo (`demo/15_huggingface_run.py`) uses the **`pipeline()`** shortcut for sentiment analysis. This exercise uses the **lower-level API** — `AutoTokenizer` + `AutoModelForSequenceClassification` — so you see what the pipeline does under the hood.

## Prerequisites

```bash
pip install -e ".[local-ml]"
```

For local development, `distilbert-base-uncased-finetuned-sst-2-english` downloads ~250MB on first use. Tests use a tiny random model and do not need network access.

## Your Task

1. Implement `load_model(model_id)` — return `(tokenizer, model)` on CPU.
2. Implement `classify(text, tokenizer, model)` — return `{"label": ..., "score": ...}`.
3. Implement `classify_batch(texts, tokenizer, model)` — list of dicts.

## Steps

1. Open `start.py` and implement the three functions.
2. Load `data/logs.txt` and classify each line.
3. Compare with the demo — same model family, different API surface.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/15-huggingface-run/test_start.py -v
```

## Stretch Goals

- Map `LABEL_0` / `LABEL_1` to human-readable NEGATIVE / POSITIVE in output.
- Batch tokenise in `classify_batch` for slightly faster inference.
