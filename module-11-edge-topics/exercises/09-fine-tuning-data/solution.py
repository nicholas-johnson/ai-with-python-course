"""
Exercise 09 — Fine-tuning Data Preparation (Solution)

Prepare training data in the JSONL chat format required
by OpenAI's fine-tuning API.
"""

import json


def format_example(example: dict, system_prompt: str) -> dict:
    """
    Convert a single training example to the chat messages format.
    """
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": example["input"]},
            {"role": "assistant", "content": example["output"]},
        ]
    }


def prepare_dataset(
    examples: list[dict],
    system_prompt: str,
    val_fraction: float = 0.1,
) -> dict:
    """
    Format all examples and split into training and validation sets.
    """
    formatted = [format_example(ex, system_prompt) for ex in examples]
    split_idx = int(len(formatted) * (1 - val_fraction))
    return {
        "train": formatted[:split_idx],
        "val": formatted[split_idx:],
    }


def write_jsonl(data: list[dict], path: str) -> int:
    """
    Write a list of dicts as JSONL (one JSON object per line).
    """
    with open(path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")
    return len(data)


def validate_jsonl(path: str) -> dict:
    """
    Validate a JSONL file for fine-tuning compatibility.
    """
    errors = []
    num_examples = 0

    with open(path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            num_examples += 1

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"Line {i + 1}: invalid JSON")
                continue

            if "messages" not in entry:
                errors.append(f"Line {i + 1}: missing 'messages' key")
                continue

            messages = entry["messages"]
            if len(messages) < 2:
                errors.append(f"Line {i + 1}: fewer than 2 messages")
                continue

            for j, msg in enumerate(messages):
                if "role" not in msg:
                    errors.append(f"Line {i + 1}, message {j}: missing 'role'")
                if "content" not in msg:
                    errors.append(f"Line {i + 1}, message {j}: missing 'content'")

    return {
        "valid": len(errors) == 0,
        "num_examples": num_examples,
        "errors": errors,
    }
