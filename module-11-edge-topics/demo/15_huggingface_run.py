"""
Module 11 — Demo: Download and run a Hugging Face model (CPU only)

Uses a pre-trained DistilBERT sentiment classifier via pipeline().
First run downloads ~250MB from Hugging Face.

Run: python module-11-edge-topics/demo/15_huggingface_run.py
Requires: pip install -e ".[local-ml]"
"""

from __future__ import annotations

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""

from transformers import pipeline

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
    separator("1. Download and load pipeline")
    print(f"Model: {MODEL_ID}")
    print("Device: CPU\n")
    classifier = pipeline(
        "sentiment-analysis",
        model=MODEL_ID,
        device=-1,
    )

    separator("2. Classify ship log lines")
    for line in LOG_LINES:
        result = classifier(line)[0]
        label = result["label"]
        score = result["score"]
        print(f"  [{label:8}] ({score:.2f})  {line}")

    print(
        "\nDone. Exercise 15 uses the lower-level tokenizer + model API instead.\n"
    )


if __name__ == "__main__":
    main()
