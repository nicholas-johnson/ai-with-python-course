# Exercise 15 — Hugging Face Run (CPU)

## Recap

### What this exercise does

Thousands of pre-trained models live on the [Hugging Face Hub](https://huggingface.co/models) — ready to download and run locally. No training needed, no API key needed, no internet needed (after the first download). This exercise uses a **sentiment analysis** model to classify text as POSITIVE or NEGATIVE.

### The demo vs. this exercise

The demo (`demo/15_huggingface_run.py`) uses the **high-level `pipeline()` shortcut** which hides all the details. This exercise uses the **lower-level API** — `AutoTokenizer` + `AutoModelForSequenceClassification` — so you understand what the pipeline does under the hood.

### Key concepts explained

**AutoTokenizer** — downloads and loads the tokenizer for a specific model. The tokenizer converts text into numbers (token IDs) that the model can process. Different models have different tokenizers, so you always load the one that matches your model.

**AutoModelForSequenceClassification** — downloads and loads a model that takes text and outputs a category (like POSITIVE/NEGATIVE). The "Auto" part means it automatically figures out the right architecture from the model name.

**Logits** — the raw output scores from the model. They're just numbers (one per class) that haven't been normalized yet. A higher logit = the model thinks that class is more likely.

**Softmax** — converts logits into probabilities that sum to 1.0. If logits are `[2.5, -1.3]`, softmax might give you `[0.98, 0.02]`, meaning 98% confidence in class 0.

### The inference flow

```
Text: "The mission was a complete success!"
        │
        ▼
  Tokenizer: convert to IDs → [101, 1996, 3260, 2001, ...]
        │
        ▼
  Model: forward pass → logits: [−2.1, 3.8]
        │
        ▼
  Softmax: normalize → probabilities: [0.003, 0.997]
        │
        ▼
  Argmax: pick highest → class 1 → "POSITIVE" (score: 0.997)
```

### What `model.eval()` and `torch.no_grad()` do

- `model.eval()` — tells the model "we're not training, we're just predicting". This disables training-specific behaviors like dropout.
- `torch.no_grad()` — tells PyTorch "don't track how inputs relate to outputs" (gradient computation). Makes inference faster and uses less memory.

You always use both together when running predictions.

## Prerequisites

```bash
pip install -e ".[local-ml]"
```

For local development, `distilbert-base-uncased-finetuned-sst-2-english` downloads ~250MB on first use. Tests use a tiny random model and do not need network access.

## What you build

Three functions in **`start.py`**:

| Function | What it does |
|---|---|
| `load_model(model_id)` | Download (if needed) and return `(tokenizer, model)` on CPU |
| `classify(text, tokenizer, model)` | Classify one text, return `{"label": ..., "score": ...}` |
| `classify_batch(texts, tokenizer, model)` | Classify a list of texts |

## Data format

Input — plain text strings:

```python
text = "The mission was a complete success!"
texts = ["Engines running perfectly.", "Total system failure detected."]
```

Output of `classify`:

```python
{"label": "POSITIVE", "score": 0.997}
```

Output of `classify_batch`:

```python
[
    {"label": "POSITIVE", "score": 0.998},
    {"label": "NEGATIVE", "score": 0.994},
]
```

The model's raw labels are `LABEL_0` (negative) and `LABEL_1` (positive). You can map them to human-readable names using `model.config.id2label`.

## Step-by-step

### 1. Implement `load_model`

Download the tokenizer and model, put the model in eval mode:

```python
def load_model(model_id="distilbert-base-uncased-finetuned-sst-2-english"):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    model.eval()
    return tokenizer, model
```

> **Important:** Always call `model.eval()` after loading for inference. Without it, the model behaves as if it's still training (random dropout, etc.).

### 2. Implement `classify`

Tokenize the text, run it through the model, convert logits to a prediction:

```python
def classify(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    pred_id = int(probs.argmax())
    score = float(probs[pred_id])
    raw_label = model.config.id2label.get(pred_id, f"LABEL_{pred_id}")
    return {"label": raw_label, "score": score}
```

**What each line does:**
- `tokenizer(text, return_tensors="pt")` — converts text to a dict of PyTorch tensors (input IDs, attention mask).
- `model(**inputs)` — runs the forward pass. The `**` unpacks the dict as keyword arguments.
- `.logits` — the raw output scores (one per class).
- `torch.softmax(logits, dim=-1)[0]` — converts to probabilities. `[0]` gets the first (and only) item in the batch.
- `probs.argmax()` — index of the highest probability.
- `model.config.id2label` — maps the index to a label string.

### 3. Implement `classify_batch`

The simplest approach — loop and call `classify` for each text:

```python
def classify_batch(texts, tokenizer, model):
    return [classify(t, tokenizer, model) for t in texts]
```

## Try it

```bash
cd module-11-edge-topics/exercises/15-huggingface-run
python start.py
```

Try classifying ship log lines: "All systems nominal, smooth sailing ahead", "Critical failure in the navigation array", "Crew morale is excellent after shore leave."

## Running Tests

```bash
pytest module-11-edge-topics/exercises/15-huggingface-run/test_start.py -v
```

## Stretch Goals

- Map `LABEL_0` / `LABEL_1` to human-readable NEGATIVE / POSITIVE in output.
- Batch tokenise in `classify_batch` for slightly faster inference (tokenize all texts at once with `padding=True`).
- Load `data/logs.txt` and classify every line, printing results in a table.

## Other small models to try

Swap `model_id` for any of these — all run on CPU in under a second per prediction:

| Model | Task | Size | Params |
| --- | --- | --- | --- |
| `distilbert-base-uncased-finetuned-sst-2-english` | Sentiment (POSITIVE/NEGATIVE) | ~250MB | 66M |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | 3-class sentiment | ~500MB | 125M |
| `sentence-transformers/all-MiniLM-L6-v2` | Sentence embeddings | ~90MB | 22M |
| `facebook/bart-large-mnli` | Zero-shot classification | ~1.6GB | 407M |
| `Helsinki-NLP/opus-mt-en-fr` | English to French translation | ~300MB | 74M |
| `google/flan-t5-small` | Instruction-tuned text generation | ~300MB | 77M |

Browse more at [huggingface.co/models](https://huggingface.co/models). For CPU inference, look for "base", "small", "distil", or "mini" in the name, and check the "Files and versions" tab for download size — anything under ~500M parameters runs comfortably on a laptop.
