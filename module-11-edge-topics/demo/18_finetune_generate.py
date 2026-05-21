"""
Module 11 — Demo: Fine-tune a causal language model locally (CPU only)

Starts from HuggingFaceTB/SmolLM2-360M-Instruct and fine-tunes it to produce
structured duty-officer summaries from raw ship log entries:

    Input:  "Summarise for the duty officer: Reactor overheating — shutdown now."
    Before: "The reactor is overheating and needs to be shut down immediately."
    After:  "ENGINEERING | URGENT | Reactor overheating. Initiate shutdown."

This shows how fine-tuning teaches the model a specific *format* and *style*
it wouldn't follow reliably from prompting alone.

How this differs from demo 14 (DistilBERT classifier):
  - Demo 14 adds a classification head and predicts a fixed label (engineering/
    medical/navigation). The output is always one of those three words.
  - This demo fine-tunes the language model itself to generate free text in
    a new format. The model learns structure, not just categories.

How causal LM fine-tuning works:
  - Prompt + response are concatenated into one token sequence.
  - Labels = same token IDs, but prompt positions are set to -100 (ignored
    by the loss). The model only learns to predict the response tokens.
  - This is called "supervised fine-tuning" (SFT).

First run downloads ~720MB from Hugging Face.

Run: python module-11-edge-topics/demo/18_finetune_generate.py
Requires: pip install -e ".[local-ml]"

Training takes ~5–10 minutes on CPU (max_steps=30).
"""

from __future__ import annotations

import logging
import os
import warnings

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path

import random

import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message="Some weights of")

MODEL_NAME = "HuggingFaceTB/SmolLM2-360M-Instruct"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "models" / "ship-summary-demo"
MAX_LENGTH = 256   # max tokens per training example (prompt + response)

SYSTEM_PROMPT = (
    "You are the duty-officer AI aboard DSS Pathfinder. "
    "Summarise ship log entries in the format: DEPT | PRIORITY | one-line summary."
)

# ---------------------------------------------------------------------------
# Training data: (log entry) → (structured duty-officer summary)
# Format: DEPARTMENT | PRIORITY | One-line summary
# ---------------------------------------------------------------------------
EXAMPLES = [
    # Engineering — routine
    {"input": "Reactor temperature stable at 5000K. All readings nominal.",
     "output": "ENGINEERING | ROUTINE | Reactor temperature nominal at 5000K."},
    {"input": "Scheduled maintenance on docking clamps completed ahead of schedule.",
     "output": "ENGINEERING | ROUTINE | Docking clamp maintenance completed early."},
    {"input": "Fuel reserves at 73%, within normal operational range.",
     "output": "ENGINEERING | ROUTINE | Fuel at 73%, no resupply needed."},
    {"input": "Engine room reports all systems operating nominally.",
     "output": "ENGINEERING | ROUTINE | All engineering systems nominal."},
    {"input": "Coolant pressure holding steady across all primary loops.",
     "output": "ENGINEERING | ROUTINE | Coolant pressure stable in all loops."},
    # Engineering — urgent
    {"input": "Reactor core temperature exceeding 6000K — immediate shutdown required.",
     "output": "ENGINEERING | URGENT | Reactor critical. Shutdown initiated."},
    {"input": "Hull breach detected on deck 7 — emergency bulkhead seals engaged.",
     "output": "ENGINEERING | URGENT | Hull breach deck 7. Bulkheads sealed."},
    {"input": "Power grid cascading failure across sectors 1 through 3.",
     "output": "ENGINEERING | URGENT | Power grid failure in sectors 1-3."},
    {"input": "Coolant leak in primary loop — manual override has failed.",
     "output": "ENGINEERING | URGENT | Primary coolant leak. Override failed."},
    {"input": "Containment field unstable — evacuate reactor deck immediately.",
     "output": "ENGINEERING | URGENT | Containment unstable. Reactor deck evacuated."},
    # Medical — routine
    {"input": "Crew member Torres reports mild headache, cleared for duty.",
     "output": "MEDICAL | ROUTINE | Torres: mild headache, fit for duty."},
    {"input": "Weekly health checks completed — all crew within normal parameters.",
     "output": "MEDICAL | ROUTINE | Weekly health checks complete, all clear."},
    {"input": "Crew member Kim cleared for EVA after completing physio.",
     "output": "MEDICAL | ROUTINE | Kim cleared for EVA post-injury physio."},
    {"input": "Sick bay restocked with standard pharmaceutical supplies.",
     "output": "MEDICAL | ROUTINE | Sick bay restocked, no shortages."},
    {"input": "Annual inoculation programme completed for all crew.",
     "output": "MEDICAL | ROUTINE | Annual inoculations complete, full crew."},
    # Medical — urgent
    {"input": "Medical emergency: officer down in engineering bay — cardiac event.",
     "output": "MEDICAL | URGENT | Officer cardiac event in engineering bay."},
    {"input": "Crew member exposed to radiation during unshielded EVA — quarantine.",
     "output": "MEDICAL | URGENT | EVA radiation exposure. Crew quarantined."},
    {"input": "Biohazard alert in medical bay — lockdown protocols activated.",
     "output": "MEDICAL | URGENT | Biohazard in medical bay. Lockdown active."},
    {"input": "Three crew members showing symptoms of unknown pathogen.",
     "output": "MEDICAL | URGENT | Three crew symptomatic, pathogen unknown."},
    {"input": "Life support oxygen dropping in section C — crew evacuating.",
     "output": "MEDICAL | URGENT | Oxygen loss in section C. Evacuation underway."},
    # Navigation — routine
    {"input": "Navigation array recalibrated following asteroid field passage.",
     "output": "NAVIGATION | ROUTINE | Nav array recalibrated post-asteroid field."},
    {"input": "Star charts updated with latest sector cartography data.",
     "output": "NAVIGATION | ROUTINE | Star charts updated for current sector."},
    {"input": "Course correction applied — arrival estimate unchanged.",
     "output": "NAVIGATION | ROUTINE | Minor course correction, ETA unchanged."},
    {"input": "Long-range sensors calibrated, no contacts on sweep.",
     "output": "NAVIGATION | ROUTINE | Long-range sensors clear, no contacts."},
    {"input": "Docking approach to Station Omega confirmed on schedule.",
     "output": "NAVIGATION | ROUTINE | Docking approach to Omega on schedule."},
    # Navigation — urgent
    {"input": "Navigation computer offline — collision risk in 12 minutes.",
     "output": "NAVIGATION | URGENT | Nav computer down. Collision risk T-12min."},
    {"input": "Unidentified vessel on intercept course — shields raised.",
     "output": "NAVIGATION | URGENT | Unidentified vessel intercepting. Shields up."},
    {"input": "Emergency FTL jump required — plot course immediately.",
     "output": "NAVIGATION | URGENT | Emergency FTL required. Plotting course."},
    {"input": "Helm control unresponsive — switching to manual backup systems.",
     "output": "NAVIGATION | URGENT | Helm unresponsive. Manual backup engaged."},
    {"input": "Gravitational anomaly detected — course change needed urgently.",
     "output": "NAVIGATION | URGENT | Gravity anomaly. Urgent course change needed."},
]

PROMPT_PREFIX = "Summarise for the duty officer: "


def separator(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")


def make_user_message(log_text: str) -> str:
    return f"{PROMPT_PREFIX}{log_text}"


def generate(user_message: str, tokenizer, model, max_new_tokens: int = 40) -> str:
    """Generate a response for a single user message."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    input_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,          # greedy — deterministic output for demo clarity
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = output_ids[0][input_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def show_samples(model, tokenizer, title: str, samples: list[str]) -> None:
    print(f"{title}\n")
    for log in samples:
        user_msg = make_user_message(log)
        response = generate(user_msg, tokenizer, model)
        print(f"  LOG:   {log}")
        print(f"  MODEL: {response}\n")


def tokenize_example(example: dict, tokenizer) -> dict:
    """
    Tokenize one training example for causal LM fine-tuning.

    The full sequence is: [prompt tokens] [response tokens]
    Labels mask the prompt tokens with -100 so the loss only
    applies to the response — the model learns to predict the
    output, not to memorise the input.
    """
    user_message = make_user_message(example["input"])

    # Full sequence: system + user + assistant response
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": example["output"]},
    ]
    full_text = tokenizer.apply_chat_template(
        full_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    # Prompt only (no response) — used to find where the response starts
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    prompt_text = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    full_enc = tokenizer(
        full_text,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length",
    )
    prompt_len = len(tokenizer(prompt_text, add_special_tokens=False)["input_ids"])

    # Build labels: -100 for prompt positions, real token IDs for response positions
    labels = list(full_enc["input_ids"])
    for i in range(min(prompt_len, len(labels))):
        labels[i] = -100
    # Also mask padding tokens
    for i, mask in enumerate(full_enc["attention_mask"]):
        if mask == 0:
            labels[i] = -100

    return {
        "input_ids": full_enc["input_ids"],
        "attention_mask": full_enc["attention_mask"],
        "labels": labels,
    }


def train(tokenizer, model) -> None:
    separator("3. Prepare dataset")
    records = [{"input": ex["input"], "output": ex["output"]} for ex in EXAMPLES]
    dataset = Dataset.from_list(records)
    tokenized = dataset.map(
        lambda ex: tokenize_example(ex, tokenizer),
        remove_columns=["input", "output"],
    )
    # Convert to a plain list of dicts with plain Python ints so we can
    # build tensors manually without going through the Trainer/accelerate stack.
    examples = [
        {k: list(v) for k, v in row.items()}
        for row in tokenized
    ]
    print(f"Training examples: {len(examples)}\n")

    separator("4. Fine-tune (short run — ~5–10 min on CPU)")
    # Manual training loop — no Trainer, no accelerate dependency.
    # Each iteration:
    #   1. Sample a small batch.
    #   2. Forward pass → model returns loss automatically when labels are given.
    #   3. Backward pass → compute gradients.
    #   4. Accumulate across N micro-batches, then update weights.
    MAX_STEPS = 30
    BATCH_SIZE = 2
    GRAD_ACCUM = 4          # effective batch size = BATCH_SIZE * GRAD_ACCUM = 8
    LOG_STEPS = 10
    LR = 2e-4

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    model.train()
    optimizer.zero_grad()

    for step in range(1, MAX_STEPS + 1):
        batch = random.sample(examples, BATCH_SIZE)
        input_ids = torch.tensor([ex["input_ids"] for ex in batch])
        attention_mask = torch.tensor([ex["attention_mask"] for ex in batch])
        labels = torch.tensor([ex["labels"] for ex in batch])

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        # Divide loss by accumulation steps so the effective gradient is the
        # same as if we'd used a larger batch directly.
        loss = outputs.loss / GRAD_ACCUM
        loss.backward()

        if step % GRAD_ACCUM == 0:
            optimizer.step()
            optimizer.zero_grad()

        if step % LOG_STEPS == 0:
            print(f"  step {step:3d}/{MAX_STEPS}  loss={outputs.loss.item():.4f}")

    # Final optimizer step in case MAX_STEPS isn't divisible by GRAD_ACCUM
    optimizer.step()
    optimizer.zero_grad()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"\nSaved to {OUTPUT_DIR}\n")


def main() -> None:
    separator("1. Load SmolLM2-360M-Instruct from Hugging Face Hub")
    print(f"Model: {MODEL_NAME}  (causal LM, 360 M params)")
    print(f"Task:  raw ship log  →  DEPT | PRIORITY | one-line summary")
    print("Device: CPU\n")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    for p in model.parameters():
        p.data = p.data.clone()
    for b in model.buffers():
        b.data = b.data.clone()

    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}\n")

    samples = [
        "Reactor core temperature exceeding 6000K — immediate shutdown required.",
        "Navigation array recalibrated following asteroid field passage.",
        "Three crew members showing symptoms of unknown pathogen.",
        "Coolant pressure holding steady across all primary loops.",
    ]

    # Before training: model responds conversationally, ignores the format
    separator("2. Before fine-tuning — SmolLM2 baseline responses")
    model.eval()
    show_samples(model, tokenizer, "Output before training:", samples)

    # Fine-tune
    train(tokenizer, model)
    model.eval()

    # After training: model follows the DEPT | PRIORITY | summary format
    separator("5. After fine-tuning — structured duty-officer summaries")
    show_samples(model, tokenizer, "Same inputs, after training:", samples)

    # Test generalisation on inputs not seen during training
    separator("6. Generalisation — inputs not seen during training")
    unseen = [
        "Warp plasma injectors venting on deck 4 — crew cleared.",
        "Officer Reyes reports fractured wrist during zero-gravity drill.",
        "Long-range sensors detecting unknown object at bearing 227.",
    ]
    show_samples(model, tokenizer, "New log entries:", unseen)

    # Interactive mode
    separator("7. Interactive mode — type your own log entries")
    print("Type a ship log entry. The fine-tuned model will summarise it.")
    print(f"Prompt prefix added automatically: '{PROMPT_PREFIX}'")
    print("Type 'quit' or Ctrl-C to exit.\n")

    while True:
        try:
            log = input("Log > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break
        if not log or log.lower() in ("quit", "exit", "q"):
            break
        user_msg = make_user_message(log)
        response = generate(user_msg, tokenizer, model)
        print(f"Out > {response}\n")

    print(
        "Done.\n"
        "Compare:\n"
        "  demo 17 — SmolLM2 chat without fine-tuning\n"
        "  demo 14 — DistilBERT classifier (fixed labels, no text generation)\n"
    )


if __name__ == "__main__":
    main()
