"""
Module 11 — Demo: Local chatbot with SmolLM2-360M-Instruct (CPU only)

Uses HuggingFaceTB/SmolLM2-360M-Instruct — a 360M-parameter causal language
model designed for instruction-following and chat. Unlike flan-t5 (which is a
task classifier), this is an autoregressive model that generates free text.

First run downloads ~720MB from Hugging Face.

Run: python module-11-edge-topics/demo/17_huggingface_generate.py
Requires: pip install -e ".[local-ml]"

Want better quality at the cost of more RAM / slower CPU?
Swap MODEL_ID for one of these — no other code changes needed:
  HuggingFaceTB/SmolLM2-1.7B-Instruct   (~3.4 GB, noticeably better)
  Qwen/Qwen2-0.5B-Instruct               (~1 GB, similar size)
  Qwen/Qwen2-1.5B-Instruct               (~3 GB, good quality)
"""

from __future__ import annotations

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"

# How many prior exchanges to keep in the prompt.
HISTORY_TURNS = 6

BASE_PROMPT = (
    "You are the AI assistant aboard the deep-space vessel DSS Pathfinder. "
    "You help the crew with questions about ship systems, navigation, medical procedures, "
    "and general knowledge. Answer clearly and concisely."
)


def build_messages(history: list[tuple[str, str]], user_message: str) -> list[dict]:
    """Build the messages list for the chat template."""
    messages = [{"role": "system", "content": BASE_PROMPT}]
    for user, assistant in history[-HISTORY_TURNS:]:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": user_message})
    return messages


def generate(messages: list[dict], tokenizer, model, max_new_tokens: int = 200) -> str:
    # apply_chat_template formats the messages into the exact string the model
    # was trained on (different models use different formats).
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
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Slice off the prompt tokens — we only want the newly generated part.
    new_tokens = output_ids[0][input_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def main() -> None:
    print(f"\nLoading {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

    for p in model.parameters():
        p.data = p.data.clone()
    for b in model.buffers():
        b.data = b.data.clone()

    model.eval()
    params = sum(p.numel() for p in model.parameters())
    print(f"Ready. {params:,} parameters. Running on CPU.")
    print(f"Memory: last {HISTORY_TURNS} turns included in each prompt.")
    print("Type a question or instruction. Type 'quit' to exit.\n")

    history: list[tuple[str, str]] = []

    while True:
        try:
            user_input = input("You   > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break
        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            break
        messages = build_messages(history, user_input)
        reply = generate(messages, tokenizer, model)
        history.append((user_input, reply))
        print(f"Model > {reply}\n")


if __name__ == "__main__":
    main()
