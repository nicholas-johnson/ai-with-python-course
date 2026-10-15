"""
Exercise 14 — Local Training (CPU)

Fine-tune a small DistilBERT classifier on ship log departments.
Uses Hugging Face Trainer — no GPU required.

TODO: Implement each function below.
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
    """
    Load training examples from a JSON file (list of {text, label}).

    Raise ValueError if any label is not engineering, medical, or navigation.
    """
    raise NotImplementedError


def build_dataset(examples: list[dict], tokenizer) -> Dataset:
    """Tokenise examples into a Hugging Face Dataset with a labels column."""
    raise NotImplementedError


def train_model(
    examples: list[dict],
    output_dir: str | Path,
    model_name: str = DEFAULT_MODEL,
    max_steps: int = 30,
) -> Path:
    """Fine-tune a sequence classifier and save tokenizer + weights to output_dir."""
    raise NotImplementedError


def predict(model_dir: str | Path, text: str) -> str:
    """Load the saved model from model_dir and return the predicted label string."""
    raise NotImplementedError
