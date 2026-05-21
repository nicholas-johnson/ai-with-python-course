"""
Module 11 — Demo: Translate ship logs with a Hugging Face model (CPU only)

Uses Helsinki-NLP/opus-mt-en-fr — a 74M-parameter English→French
translation model from the OPUS project.
First run downloads ~300MB from Hugging Face.

Run: python module-11-edge-topics/demo/16_huggingface_translate.py
Requires: pip install -e ".[local-ml]"
"""

from __future__ import annotations

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_ID = "Helsinki-NLP/opus-mt-en-fr"

LOG_LINES = [
    "Reactor temperature stable at 5000K.",
    "Hull breach detected on deck 7 — seal bulkheads now.",
    "Fuel reserves look fine for the next two weeks.",
    "Medical emergency: officer down in engineering bay.",
    "Routine calibration finished ahead of schedule.",
    "All personnel report to stations — red alert.",
]


def separator(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")


def translate(text: str, tokenizer, model) -> str:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_new_tokens=128)
    return tokenizer.decode(output_ids[0], skip_special_tokens=True)


def main() -> None:
    separator("1. Download translation model from Hugging Face Hub")
    print(f"Model: {MODEL_ID}")
    print("Task:  English → French")
    print("Device: CPU\n")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)

    for p in model.parameters():
        p.data = p.data.clone()
    for b in model.buffers():
        b.data = b.data.clone()

    model.eval()
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}\n")

    separator("2. Translate ship log lines")
    for line in LOG_LINES:
        french = translate(line, tokenizer, model)
        print(f"  EN: {line}")
        print(f"  FR: {french}\n")

    separator("3. Interactive mode — try your own text")
    print("Type an English sentence and the model will translate it to French.")
    print("Type 'quit' or Ctrl-C to exit.\n")

    while True:
        try:
            text = input("EN > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break
        if not text or text.lower() in ("quit", "exit", "q"):
            break
        french = translate(text, tokenizer, model)
        print(f"FR > {french}\n")

    print("Done.\n")


if __name__ == "__main__":
    main()
