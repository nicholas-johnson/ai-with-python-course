"""
Module 11 — Demo: Train a small classifier locally (CPU only)

Fine-tunes DistilBERT on ship log lines: urgent vs routine.
First run downloads ~250MB from Hugging Face.

Run: python module-11-edge-topics/demo/14_train_local.py
Requires: pip install -e ".[local-ml]"
"""

from __future__ import annotations

import logging
import os
import warnings

os.environ["CUDA_VISIBLE_DEVICES"] = ""

from pathlib import Path

import torch
from datasets import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message="Some weights of")

MODEL_NAME = "distilbert-base-uncased"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "models" / "ship-urgency-demo"
LABEL2ID = {"routine": 0, "urgent": 1}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}

EXAMPLES = [
    {"text": "Reactor temperature stable at 5000K.", "label": "routine"},
    {"text": "Reactor core temperature exceeding 6000K — shutdown required.", "label": "urgent"},
    {"text": "Routine navigation calibration completed.", "label": "routine"},
    {"text": "Hull breach detected on deck 7 — seal bulkheads now.", "label": "urgent"},
    {"text": "Crew shift change at 1800 hours.", "label": "routine"},
    {"text": "FTL-4092 emergency protocol activated immediately.", "label": "urgent"},
    {"text": "Fuel reserves at 73%, within normal range.", "label": "routine"},
    {"text": "Life support failure in section C — evacuate crew.", "label": "urgent"},
    {"text": "Weekly hull inspection shows no new damage.", "label": "routine"},
    {"text": "Unidentified vessel on intercept course — weapons ready.", "label": "urgent"},
    {"text": "Galley inventory restocked from Station Omega.", "label": "routine"},
    {"text": "Coolant leak in primary loop — manual override failed.", "label": "urgent"},
    {"text": "Science team published sector survey notes.", "label": "routine"},
    {"text": "Medical emergency: officer down in engineering bay.", "label": "urgent"},
    {"text": "Ambient life support readings nominal.", "label": "routine"},
    {"text": "Navigation computer offline — collision risk in 12 minutes.", "label": "urgent"},
    {"text": "Scheduled maintenance on deck 3 airlocks.", "label": "routine"},
    {"text": "Radiation spike in cargo bay — quarantine required.", "label": "urgent"},
    {"text": "Communications test with home base successful.", "label": "routine"},
    {"text": "Distress signal received from escape pod bay 4.", "label": "urgent"},
    {"text": "Star map updated with latest cartography data.", "label": "routine"},
    {"text": "All personnel report to stations — red alert.", "label": "urgent"},
    {"text": "Crew morale report filed — all departments green.", "label": "routine"},
    {"text": "Fire suppression failed on deck 5.", "label": "urgent"},
    {"text": "Docking clamps released on schedule.", "label": "routine"},
    {"text": "Power grid cascading failure across sectors 1-3.", "label": "urgent"},
    {"text": "Water recycling system operating at 98% efficiency.", "label": "routine"},
    {"text": "Containment field unstable — evacuate reactor deck.", "label": "urgent"},
    {"text": "Library database synced with Earth archives.", "label": "routine"},
    {"text": "Hostile boarders detected in shuttle bay.", "label": "urgent"},
    {"text": "Artificial gravity steady at 1.0g on all decks.", "label": "routine"},
    {"text": "Oxygen levels dropping in sleeping quarters.", "label": "urgent"},
    {"text": "Sensor array calibration passed — no anomalies.", "label": "routine"},
    {"text": "Emergency FTL jump required — plot course now.", "label": "urgent"},
    {"text": "Shore leave roster posted for next station stop.", "label": "routine"},
    {"text": "Structural integrity at 40% on starboard hull.", "label": "urgent"},
    {"text": "Quarterly fire drill completed in 4 minutes.", "label": "routine"},
    {"text": "Captain orders immediate full stop.", "label": "urgent"},
    {"text": "Engine room reports all systems nominal.", "label": "routine"},
    {"text": "Biohazard alert in medical bay — lock down.", "label": "urgent"},
]


def separator(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")


def tokenize_dataset(examples: dict, tokenizer) -> dict:
    return tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=64,
    )


def train() -> Path:
    separator("1. Load model and tokenizer")
    print(f"Model: {MODEL_NAME} (CPU only)")
    print("Loading pre-trained encoder and adding a fresh classification head...\n")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Trainable:  {sum(p.numel() for p in model.parameters() if p.requires_grad):,}\n")

    separator("2. Prepare dataset")
    records = [
        {"text": ex["text"], "label": LABEL2ID[ex["label"]]}
        for ex in EXAMPLES
    ]
    dataset = Dataset.from_list(records)
    tokenized = dataset.map(
        lambda batch: tokenize_dataset(batch, tokenizer),
        batched=True,
    )
    tokenized = tokenized.rename_column("label", "labels")
    print(f"Training examples: {len(tokenized)}\n")

    separator("3. Train (short run — ~2–5 min on CPU)")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        max_steps=30,
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
        train_dataset=tokenized,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"\nSaved to {OUTPUT_DIR}\n")
    return OUTPUT_DIR


def predict(model_dir: Path, text: str) -> tuple[str, float]:
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    pred_id = int(probs.argmax())
    return ID2LABEL[pred_id], float(probs[pred_id])


def interactive_loop(model_dir: Path) -> None:
    separator("5. Interactive mode — try your own log lines")
    print("Type a ship log line and the model will classify it.")
    print("Type 'quit' or Ctrl-C to exit.\n")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()

    while True:
        try:
            text = input("Log > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break
        if not text or text.lower() in ("quit", "exit", "q"):
            break

        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
        with torch.no_grad():
            logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        pred_id = int(probs.argmax())
        label = ID2LABEL[pred_id]
        confidence = float(probs[pred_id])

        bar = "█" * int(confidence * 20) + "░" * (20 - int(confidence * 20))
        color = "\033[91m" if label == "urgent" else "\033[92m"
        reset = "\033[0m"
        print(f"  {color}{label.upper():>7}{reset}  {bar}  {confidence:.0%}\n")


def main() -> None:
    model_dir = train()

    separator("4. Predict on new log lines")
    samples = [
        "Coolant pressure normal on all decks.",
        "Reactor temperature critical — initiate emergency shutdown.",
        "Crew completed routine drill in shuttle bay.",
        "Shields failing — brace for impact.",
        "Cargo manifest updated for sector 9.",
    ]
    print("Classifying sample log lines with the fine-tuned model:\n")
    for text in samples:
        label, score = predict(model_dir, text)
        indicator = "🔴" if label == "urgent" else "🟢"
        print(f"  {indicator} [{label:7}] ({score:.2f})  {text}")

    interactive_loop(model_dir)
    print("Done. Compare with Exercise 14 (3-class department labels).\n")


if __name__ == "__main__":
    main()
