"""
Module 11 — Demo: Download and run a Hugging Face model (CPU only)

Uses a pre-trained DistilBERT sentiment classifier from Hugging Face Hub.
First run downloads ~250MB.

Run: python module-11-edge-topics/demo/15_huggingface_run.py
Requires: pip install -e ".[local-ml]"
"""

from __future__ import annotations

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = "distilbert-base-uncased-finetuned-sst-2-english"

LOG_LINES = [
    "Reactor temperature stable — another quiet watch.",
    "Hull breach on deck 7 — this is a disaster.",
    "Fuel reserves look fine for the next two weeks.",
    "We lost three crew members in the explosion.",
    "Routine calibration finished ahead of schedule.",
]


def separator(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")


def main() -> None:
    separator("1. Download model from Hugging Face Hub")
    print(f"Model: {MODEL_ID}")
    print("Device: CPU\n")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)

    # Workaround: safetensors weights are memory-mapped, which can trigger
    # SIGBUS during inference on Apple Silicon. Clone tensors into regular
    # memory before running the forward pass.
    for p in model.parameters():
        p.data = p.data.clone()
    for b in model.buffers():
        b.data = b.data.clone()

    model.eval()
    id2label = model.config.id2label
    print(f"Labels: {id2label}")
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}\n")

    separator("2. Classify ship log lines")
    for line in LOG_LINES:
        inputs = tokenizer(line, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        pred_id = int(probs.argmax())
        label = id2label[pred_id]
        score = float(probs[pred_id])
        print(f"  [{label:8}] ({score:.2f})  {line}")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
