"""
Exercise 15 — Hugging Face Run (CPU)

Download a pre-trained model from Hugging Face and run inference
without the high-level pipeline() wrapper.

TODO: Implement each function below.
"""

from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
SST2_LABELS = {"LABEL_0": "NEGATIVE", "LABEL_1": "POSITIVE"}


def load_model(model_id: str = DEFAULT_MODEL) -> tuple:
    """Download (if needed) and return (tokenizer, model) on CPU."""
    raise NotImplementedError


def classify(text: str, tokenizer, model) -> dict:
    """
    Run one text through the model.

    Returns {"label": str, "score": float} for the predicted class.
    """
    raise NotImplementedError


def classify_batch(texts: list[str], tokenizer, model) -> list[dict]:
    """Classify each text; return a list of {label, score} dicts."""
    raise NotImplementedError
