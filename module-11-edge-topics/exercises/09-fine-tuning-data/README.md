# Exercise 09 — Fine-tuning Data Preparation

## Recap

### What is fine-tuning?

Fine-tuning takes a pre-trained model (like GPT-4o-mini) and trains it further on *your* examples so it learns your specific patterns, tone, or domain knowledge. After fine-tuning, the model behaves more like your examples without needing long prompts every time.

### The most important step: data preparation

Fine-tuning is only as good as your training data. The process requires examples in a specific format — **JSONL** (JSON Lines), where each line is a complete training example in the chat message format.

### What is JSONL?

JSONL is just a text file where every line is a separate JSON object. No commas between lines, no wrapping array:

```
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Each line represents one training conversation: a system prompt (optional), a user message (the input), and an assistant message (the desired output the model should learn to produce).

### The chat messages format

Each training example has a `"messages"` array with three roles:

```python
{
    "messages": [
        {"role": "system", "content": "You are a ship log classifier."},
        {"role": "user", "content": "Warp drive offline, running on impulse only."},
        {"role": "assistant", "content": "Category: engineering\nPriority: high"},
    ]
}
```

- **system** — sets the persona/instructions (same for all examples).
- **user** — the input your model will receive.
- **assistant** — the output you want the model to learn to produce.

### Quality over quantity

50 high-quality, diverse examples beats 500 sloppy ones. Each example should:
- Be representative of real usage
- Have a clear, correct output
- Cover different scenarios (don't repeat the same pattern 50 times)

## What you build

Four functions in **`start.py`**:

| Function | What it does |
|---|---|
| `format_example(example, system_prompt)` | Convert one `{input, output}` dict to the chat messages format |
| `prepare_dataset(examples, system_prompt, val_fraction)` | Format all examples and split into train/validation sets |
| `write_jsonl(data, path)` | Write formatted data to a JSONL file |
| `validate_jsonl(path)` | Read a JSONL file and check it's valid for fine-tuning |

## Data format

Your raw training examples look like this:

```python
examples = [
    {"input": "Warp drive offline, running on impulse only.", "output": "engineering"},
    {"input": "Crew member reports headache after away mission.", "output": "medical"},
    {"input": "Asteroid field detected, plotting new course.", "output": "navigation"},
]
```

After `format_example`, each becomes:

```python
{
    "messages": [
        {"role": "system", "content": "Classify this ship log into a department."},
        {"role": "user", "content": "Warp drive offline, running on impulse only."},
        {"role": "assistant", "content": "engineering"},
    ]
}
```

`prepare_dataset` returns a dict with train/val splits:

```python
{"train": [... 90% of examples ...], "val": [... 10% of examples ...]}
```

`validate_jsonl` returns a validation report:

```python
{"valid": True, "num_examples": 45, "errors": []}
# or
{"valid": False, "num_examples": 43, "errors": ["Line 12: missing 'messages' key"]}
```

## Step-by-step

### 1. Implement `format_example`

Take a raw example and wrap it in the messages format:

```python
def format_example(example: dict, system_prompt: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": example["input"]},
            {"role": "assistant", "content": example["output"]},
        ]
    }
```

### 2. Implement `prepare_dataset`

Format all examples, then split at a percentage point:

```python
def prepare_dataset(examples, system_prompt, val_fraction=0.1):
    formatted = [format_example(ex, system_prompt) for ex in examples]
    split_idx = int(len(formatted) * (1 - val_fraction))
    return {"train": formatted[:split_idx], "val": formatted[split_idx:]}
```

> **Important:** A validation set (typically 10% of data) lets you check if the model is actually learning vs. just memorising. Always include one.

### 3. Implement `write_jsonl`

Write one JSON object per line — no pretty-printing, no trailing commas:

```python
def write_jsonl(data: list[dict], path: str) -> int:
    with open(path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")
    return len(data)
```

### 4. Implement `validate_jsonl`

Read the file line by line. For each line, check:
1. Is it valid JSON?
2. Does it have a `"messages"` key?
3. Does `"messages"` have at least 2 entries?
4. Does each message have `"role"` and `"content"`?

Collect errors with line numbers so users can fix them:

```python
try:
    entry = json.loads(line)
except json.JSONDecodeError:
    errors.append(f"Line {i + 1}: invalid JSON")
    continue

if "messages" not in entry:
    errors.append(f"Line {i + 1}: missing 'messages' key")
```

## Try it

```bash
cd module-11-edge-topics/exercises/09-fine-tuning-data
python start.py
```

## Running Tests

```bash
pytest module-11-edge-topics/exercises/09-fine-tuning-data/test_start.py -v
```

## Stretch Goals

- Add deduplication to remove near-identical examples.
- Add token counting to estimate fine-tuning cost (OpenAI charges per token).
- Implement stratified train/validation splitting (equal label distribution in both sets).
