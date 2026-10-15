"""
Exercise 09 — Fine-tuning Data Preparation

Prepare training data in the JSONL chat format required
by OpenAI's fine-tuning API.
"""

import json


def format_example(example: dict, system_prompt: str) -> dict:
    """
    Convert a single training example to the chat messages format.

    Args:
        example: Dict with "input" and "output" keys.
        system_prompt: The system message for all examples.

    Returns:
        Dict with a "messages" key containing a list of:
        - {"role": "system", "content": system_prompt}
        - {"role": "user", "content": example["input"]}
        - {"role": "assistant", "content": example["output"]}

    TODO:
    - Create the messages list with the three roles
    - Return a dict with a "messages" key
    """
    # TODO: implement example formatting
    pass


def prepare_dataset(
    examples: list[dict],
    system_prompt: str,
    val_fraction: float = 0.1,
) -> dict:
    """
    Format all examples and split into training and validation sets.

    Args:
        examples: List of dicts with "input" and "output" keys.
        system_prompt: System prompt for all examples.
        val_fraction: Fraction of examples for validation (0.0-1.0).

    Returns:
        Dict with "train" and "val" keys, each containing a list of
        formatted examples.

    TODO:
    - Format each example using format_example
    - Split into train and val based on val_fraction
    - The split point is int(len(examples) * (1 - val_fraction))
    - Return a dict with "train" and "val" lists
    """
    # TODO: implement dataset preparation
    pass


def write_jsonl(data: list[dict], path: str) -> int:
    """
    Write a list of dicts as JSONL (one JSON object per line).

    Args:
        data: List of dicts to write.
        path: Output file path.

    Returns:
        Number of lines written.

    TODO:
    - Open the file for writing
    - Write each dict as a JSON line
    - Return the count of lines written
    """
    # TODO: implement JSONL writing
    pass


def validate_jsonl(path: str) -> dict:
    """
    Validate a JSONL file for fine-tuning compatibility.

    Checks:
    - Each line is valid JSON
    - Each entry has a "messages" key
    - Messages list has at least 2 entries (user + assistant)
    - Each message has "role" and "content" keys

    Returns:
        Dict with:
        - "valid": bool
        - "num_examples": int
        - "errors": list[str]

    TODO:
    - Read each line and validate it
    - Collect all errors
    - Return the validation result
    """
    # TODO: implement validation
    pass
