"""
Exercise 09 — Fine-tuning Data Preparation

Prepare training data in the JSONL chat format required
by OpenAI's fine-tuning API.

TODO: Implement each function below.
"""

import json


def format_example(example: dict, system_prompt: str) -> dict:
    """
    Convert a single training example to the chat messages format.

    Return a dict with a "messages" key containing a list of
    system, user, and assistant messages.
    """
    raise NotImplementedError


def prepare_dataset(
    examples: list[dict],
    system_prompt: str,
    val_fraction: float = 0.1,
) -> dict:
    """
    Format all examples and split into training and validation sets.

    Returns {"train": [...], "val": [...]}.
    """
    raise NotImplementedError


def write_jsonl(data: list[dict], path: str) -> int:
    """
    Write a list of dicts as JSONL (one JSON object per line).
    Returns the number of entries written.
    """
    raise NotImplementedError


def validate_jsonl(path: str) -> dict:
    """
    Validate a JSONL file for fine-tuning compatibility.

    Check that each line is valid JSON, has a "messages" key with
    at least 2 messages, and every message has "role" and "content".

    Returns {"valid": bool, "num_examples": int, "errors": [...]}.
    """
    raise NotImplementedError
