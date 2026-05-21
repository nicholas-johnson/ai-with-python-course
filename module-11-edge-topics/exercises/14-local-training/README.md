# Exercise 14 — Local Training (CPU)

## Recap

You can fine-tune a small transformer on your laptop — no GPU and no cloud API. This exercise trains **DistilBERT** to classify ship logs into **engineering**, **medical**, or **navigation** departments using Hugging Face `Trainer`.

The demo (`demo/14_train_local.py`) does a similar **urgent vs routine** binary task; here you wire the same pattern for three classes.

## Prerequisites

```bash
pip install -e ".[local-ml]"
```

First run downloads the base model (~250MB). Training uses CPU only and should finish in a few minutes with `max_steps=30`.

## Your Task

1. Implement `load_examples(path)` — read `data/labels.json`.
2. Implement `build_dataset(examples, tokenizer)` — tokenise with `max_length=64`.
3. Implement `train_model(...)` — `Trainer` with `use_cpu=True`, save to `output_dir`.
4. Implement `predict(model_dir, text)` — load saved model and return label string.

## Steps

1. Open `start.py` and read the label mapping (`LABEL2ID`).
2. Compare with `solution.py` only if stuck.
3. Train to `models/ship-dept` (create the folder or pass any path).
4. Call `predict` on a few lines of your own.

## Running Tests

Tests use `prajjwal1/bert-tiny` for speed (not DistilBERT):

```bash
pytest module-11-edge-topics/exercises/14-local-training/test_start.py -v
```

## Stretch Goals

- Add a validation split and log eval accuracy.
- Try `max_steps=100` and compare predictions before/after.
