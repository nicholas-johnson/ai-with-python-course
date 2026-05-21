"""
Exercise 15 — Hugging Face Run (solution)
"""

from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
# SST-2 labels: LABEL_0 = negative, LABEL_1 = positive
SST2_LABELS = {"LABEL_0": "NEGATIVE", "LABEL_1": "POSITIVE"}


def load_model(model_id: str = DEFAULT_MODEL) -> tuple:
    """Download (if needed) and return (tokenizer, model) on CPU."""
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    model.eval()
    return tokenizer, model


def _normalize_label(raw: str) -> str:
    return SST2_LABELS.get(raw, raw)


def classify(text: str, tokenizer, model) -> dict:
    """
    Run one text through the model.

    Returns {"label": str, "score": float} where score is the winning class probability.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    pred_id = int(probs.argmax())
    score = float(probs[pred_id])
    raw_label = model.config.id2label.get(pred_id, f"LABEL_{pred_id}")
    return {"label": _normalize_label(raw_label), "score": score}


def classify_batch(texts: list[str], tokenizer, model) -> list[dict]:
    """Classify each text; return a list of {label, score} dicts."""
    return [classify(t, tokenizer, model) for t in texts]


def load_logs(path: str | Path) -> list[str]:
    """Load non-empty lines from a text file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]
