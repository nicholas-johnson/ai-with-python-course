"""
Exercise 14 — Local Training (solution)
"""

from __future__ import annotations

import json
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

LABEL2ID = {"engineering": 0, "medical": 1, "navigation": 2}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
DEFAULT_MODEL = "distilbert-base-uncased"


def load_examples(path: str | Path) -> list[dict]:
    """Load training examples from a JSON file (list of {text, label})."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item["label"] not in LABEL2ID:
            raise ValueError(f"Unknown label: {item['label']}")
    return data


def build_dataset(examples: list[dict], tokenizer) -> Dataset:
    """Tokenise examples into a Hugging Face Dataset with labels column."""
    records = [
        {"text": ex["text"], "labels": LABEL2ID[ex["label"]]}
        for ex in examples
    ]
    dataset = Dataset.from_list(records)

    def tokenize(batch: dict) -> dict:
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=64,
        )

    tokenized = dataset.map(tokenize, batched=True)
    return tokenized


def train_model(
    examples: list[dict],
    output_dir: str | Path,
    model_name: str = DEFAULT_MODEL,
    max_steps: int = 30,
) -> Path:
    """Fine-tune a sequence classifier and save to output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    train_ds = build_dataset(examples, tokenizer)

    args = TrainingArguments(
        output_dir=str(output_dir),
        max_steps=max_steps,
        per_device_train_batch_size=8,
        learning_rate=2e-5,
        logging_steps=10,
        save_strategy="no",
        use_cpu=True,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        tokenizer=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    return output_dir


def predict(model_dir: str | Path, text: str) -> str:
    """Return the predicted department label for a single text."""
    import torch

    model_dir = Path(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    pred_id = int(logits.argmax(dim=-1).item())
    return ID2LABEL[pred_id]
