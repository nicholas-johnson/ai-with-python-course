# Exercise 09 — Fine-tuning Data Preparation

## Recap

Fine-tuning trains a model on your examples so domain-specific patterns become built-in. The most critical step is **data preparation** — formatting high-quality input-output pairs into the JSONL format that fine-tuning APIs expect. Quality beats quantity.

## Your Task

1. Implement `format_example(example, system_prompt)` — convert a single example to chat format.
2. Implement `prepare_dataset(examples, system_prompt)` — format an entire dataset.
3. Implement `write_jsonl(data, path)` — write formatted data to a JSONL file.
4. Implement `validate_jsonl(path)` — validate a JSONL file for fine-tuning.

## Steps

1. Open `start.py` and review the expected format.
2. Implement `format_example`: create a messages array with system, user, and assistant roles.
3. Implement `prepare_dataset`: format all examples and optionally split train/validation.
4. Implement `write_jsonl`: write one JSON object per line.
5. Implement `validate_jsonl`: check each line is valid JSON with the required structure.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/09-fine-tuning-data/test_start.py -v
```

## Stretch Goals

- Add deduplication to remove near-identical examples.
- Add token counting to estimate fine-tuning cost.
- Implement stratified train/validation splitting.
