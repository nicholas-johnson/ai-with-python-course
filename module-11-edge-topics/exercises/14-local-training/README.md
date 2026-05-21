# Exercise 14 — Local Training (CPU)

## Recap

### What this exercise does

You're going to **fine-tune a small language model on your own laptop** — no GPU, no cloud API, no internet needed (after the initial download). The model learns to classify ship log entries into three departments: **engineering**, **medical**, or **navigation**.

### Key concepts explained

**Fine-tuning** means taking a model that already knows language (it was pre-trained on billions of words) and training it a bit more on your specific task. It's like hiring someone who already speaks English and teaching them your company's jargon.

**DistilBERT** is a small, fast version of the BERT language model. It's 250MB (vs. GPT-4's hundreds of gigabytes) and runs on a CPU in seconds. We're not using it for chat — we're using it as a text classifier.

**Tokenizer** — before a model can read text, the text must be converted to numbers. A tokenizer splits text into pieces (tokens) and maps each piece to a number. "Warp drive offline" might become `[2748, 3298, 9087]`.

**Hugging Face Trainer** is a helper class that handles the training loop for you — forward pass, loss calculation, backward pass, weight updates. You give it a model, data, and settings; it does the rest.

### The training data format

Your labeled examples are a JSON file — each entry has a `"text"` and a `"label"`:

```json
[
    {"text": "Warp drive offline, switching to impulse power", "label": "engineering"},
    {"text": "Crew member reports nausea after away mission", "label": "medical"},
    {"text": "Asteroid field detected, plotting evasive course", "label": "navigation"}
]
```

### The training flow

```
Load examples (JSON) → Tokenize texts → Create Dataset → Train with Trainer → Save model
```

After training, you load the saved model and classify new text:

```
"Plasma conduit ruptured on deck 7" → model → "engineering"
```

## Prerequisites

```bash
pip install -e ".[local-ml]"
```

First run downloads the base model (~250MB). Training uses CPU only and should finish in a few minutes with `max_steps=30`.

## What you build

Four functions in **`start.py`**:

| Function | What it does |
|---|---|
| `load_examples(path)` | Read the training data JSON file |
| `build_dataset(examples, tokenizer)` | Tokenize examples into a Hugging Face Dataset |
| `train_model(examples, output_dir, model_name, max_steps)` | Fine-tune and save the model |
| `predict(model_dir, text)` | Load a saved model and classify one text |

The label mapping is already defined for you:

```python
LABEL2ID = {"engineering": 0, "medical": 1, "navigation": 2}
ID2LABEL = {0: "engineering", 1: "medical", 2: "navigation"}
```

## Step-by-step

### 1. Implement `load_examples`

Read the JSON file and validate that every label exists in `LABEL2ID`:

```python
def load_examples(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item["label"] not in LABEL2ID:
            raise ValueError(f"Unknown label: {item['label']}")
    return data
```

### 2. Implement `build_dataset`

Convert examples to a Hugging Face `Dataset`, then tokenize:

```python
from datasets import Dataset

def build_dataset(examples, tokenizer):
    records = [{"text": ex["text"], "labels": LABEL2ID[ex["label"]]} for ex in examples]
    dataset = Dataset.from_list(records)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=64)

    tokenized = dataset.map(tokenize, batched=True)
    return tokenized
```

> **Important:** The column must be called `"labels"` (not `"label"`) — that's what the Trainer expects.

### 3. Implement `train_model`

Load the tokenizer and model, build the dataset, configure training, and run:

```python
def train_model(examples, output_dir, model_name="distilbert-base-uncased", max_steps=30):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    train_ds = build_dataset(examples, tokenizer)

    args = TrainingArguments(
        output_dir=str(output_dir),
        max_steps=max_steps,
        per_device_train_batch_size=8,
        learning_rate=2e-5,
        logging_steps=10,
        save_strategy="no",
        use_cpu=True,
        report_to="none",
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, tokenizer=tokenizer)
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    return output_dir
```

> **Important:** Set `use_cpu=True` — this ensures training works on any machine. Set `report_to="none"` to avoid needing wandb or other logging services.

### 4. Implement `predict`

Load the saved model and run inference on a single text:

```python
import torch

def predict(model_dir, text):
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    pred_id = int(logits.argmax(dim=-1).item())
    return ID2LABEL[pred_id]
```

**What's happening:**
- `return_tensors="pt"` means return PyTorch tensors (not plain lists).
- `torch.no_grad()` tells PyTorch not to track gradients (faster, uses less memory — we're just predicting, not training).
- `logits` are raw scores for each class. `argmax` picks the highest-scoring class.

## Try it

```bash
cd module-11-edge-topics/exercises/14-local-training
python start.py
```

Try classifying your own ship logs: "Hull breach on deck 3", "Patient showing signs of radiation exposure", "Star charts need recalibration."

## Running Tests

Tests use `prajjwal1/bert-tiny` for speed (not DistilBERT):

```bash
pytest module-11-edge-topics/exercises/14-local-training/test_start.py -v
```

## Stretch Goals

- Add a validation split and log eval accuracy during training.
- Try `max_steps=100` and compare predictions before/after.
- Add a confidence score (use `torch.softmax` on the logits to get probabilities).

## Extensions

Once the basic exercise works, try one of these. Each keeps the same overall pattern — load a base model, attach a classification head, train on `{text, label}` pairs — but swaps the model or training method.

### Extension 1: Compare lightweight encoders

**Goal:** See how model size affects speed vs. accuracy on the same ship-log task.

| Base model | What it does | Size |
|---|---|---|
| `prajjwal1/bert-tiny` | A stripped-down BERT for experiments. Very fast, lower accuracy. | ~4MB |
| `distilbert-base-uncased` | Distilled BERT — keeps most of BERT's quality at ~40% of the size. Default for this exercise. | ~250MB |
| `google/mobilebert-uncased` | Built for phones/edge devices. Fewer parameters, designed for low latency. | ~100MB |

**How to fine-tune:** Change only `model_name` in `train_model()`. Everything else stays the same — `AutoModelForSequenceClassification.from_pretrained()` adds a fresh classification layer on top, and `Trainer` updates all weights (or mostly all) on your labels.

```python
for model_name in ["prajjwal1/bert-tiny", "distilbert-base-uncased", "google/mobilebert-uncased"]:
    train_model(examples, f"models/compare-{model_name.split('/')[-1]}", model_name=model_name)
```

Train each for the same `max_steps`, then run the same test sentences through `predict()` and compare labels and wall-clock time.

---

### Extension 2: Upgrade to RoBERTa

**Goal:** Trade a bit more compute for better classification quality.

| Base model | What it does | Size |
|---|---|---|
| `distilroberta-base` | Distilled RoBERTa — good balance of speed and accuracy. | ~320MB |
| `roberta-base` | RoBERTa (Robustly Optimized BERT). Same architecture family as BERT but trained with better pre-training tricks (no NSP task, dynamic masking, larger batches). Often beats BERT on classification. | ~480MB |

**How to fine-tune:** Identical code path to DistilBERT. RoBERTa uses a different tokenizer (byte-level BPE instead of WordPiece), but Hugging Face handles that when you call `AutoTokenizer.from_pretrained(model_name)`.

```python
train_model(examples, "models/ship-dept-roberta", model_name="distilroberta-base", max_steps=50)
```

> **Tip:** RoBERTa models usually want `max_length=128` or `256` rather than `64` if your log lines are long — update `build_dataset()` accordingly.

---

### Extension 3: Domain-specific pre-training (medical logs)

**Goal:** Start from a model that already "speaks" medical language, then teach it your three-way department labels.

| Base model | What it does | Size |
|---|---|---|
| `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract` | BERT pre-trained on PubMed abstracts and biomedical papers. Strong on clinical vocabulary (symptoms, diagnoses, treatments). | ~420MB |
| `emilyalsentzer/Bio_ClinicalBERT` | BERT pre-trained on MIMIC clinical notes. Good for patient-report-style text. | ~420MB |

**How to fine-tune:** Same `AutoModelForSequenceClassification` + `Trainer` flow. The base weights already encode medical terms; you're only teaching the model *which department bucket* each log belongs in. This often needs fewer steps than generic BERT when many examples are medical.

Filter `data/labels.json` to mostly medical examples, or add more medical lines, then:

```python
train_model(
    examples,
    "models/ship-dept-biomed",
    model_name="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract",
    max_steps=40,
)
```

Compare predictions on medical test lines vs. a model trained from plain `distilbert-base-uncased`.

---

### Extension 4: Binary urgency classifier (match the demo)

**Goal:** Fine-tune for **two** classes — **urgent** vs **routine** — like `demo/14_train_local.py`.

| Base model | What it does | Size |
|---|---|---|
| `distilbert-base-uncased` | General English encoder; works well for binary ship-log urgency. | ~250MB |

**How to fine-tune:**

1. Change the label map to two classes:

```python
LABEL2ID = {"routine": 0, "urgent": 1}
ID2LABEL = {0: "routine", 1: "urgent"}
```

2. Use (or create) a JSON file with `"label": "urgent"` or `"routine"` on each line.
3. Pass `num_labels=2` when loading the model (same as now, but with two labels).
4. Save to a separate folder, e.g. `models/ship-urgency`.

The fine-tuning mechanics are unchanged — only the number of output neurons and your training data differ.

---

### Extension 5: Parameter-efficient fine-tuning with LoRA

**Goal:** Train only a tiny adapter instead of the full model. Uses less memory and can reduce overfitting on small datasets.

| Base model | What it does | Size |
|---|---|---|
| `distilbert-base-uncased` | Frozen backbone; small LoRA matrices injected into attention layers. | ~250MB base + ~1MB adapters |

**What LoRA is:** Low-Rank Adaptation adds small trainable matrices to each layer while **freezing** the original weights. You fine-tune thousands of parameters instead of millions.

**How to fine-tune:** Install PEFT (`pip install peft`), wrap the model, then pass it to `Trainer`:

```python
from peft import LoraConfig, get_peft_model

model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=3, id2label=ID2LABEL, label2id=LABEL2ID,
)
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_lin", "v_lin"],  # DistilBERT attention modules
    lora_dropout=0.1,
    task_type="SEQ_CLS",
)
model = get_peft_model(model, lora_config)
# Then Trainer(model=model, ...) as usual
```

Save with `model.save_pretrained(output_dir)`. To load for `predict()`, use `PeftModel.from_pretrained(base_model, adapter_dir)`.

> **Note:** `target_modules` names differ per architecture — for RoBERTa use `["query", "value"]`; check the model's layer names if training fails.

---

### Extension 6: Multilingual ship logs with XLM-RoBERTa

**Goal:** Classify logs written in more than one language without training a separate model per language.

| Base model | What it does | Size |
|---|---|---|
| `xlm-roberta-base` | Cross-lingual encoder trained on 100+ languages. Same vector space for English, French, Spanish, etc. | ~1.1GB |
| `distilbert-base-multilingual-cased` | Smaller multilingual BERT; slower than XLM-R on hard tasks but lighter on disk/RAM. | ~680MB |

**How to fine-tune:** Same sequence-classification pipeline. Add examples in multiple languages with the **same** label strings (`engineering`, `medical`, `navigation`):

```json
[
    {"text": "Warp drive offline", "label": "engineering"},
    {"text": "Moteur de distorsion hors ligne", "label": "engineering"},
    {"text": "Tripulante con náuseas", "label": "medical"}
]
```

Use `max_length=128` — non-English text often tokenizes to more subwords than English. Train with `model_name="xlm-roberta-base"` and test that an English-trained pattern generalizes to French/Spanish log lines.

---

### Quick reference: which extension when?

| If you want… | Start with… |
|---|---|
| Fastest experiments on a laptop | Extension 1 (`bert-tiny` or `mobilebert`) |
| Best accuracy on English logs | Extension 2 (`distilroberta-base`) |
| Heavy medical wording in the data | Extension 3 (PubMedBERT or ClinicalBERT) |
| Urgent vs routine (like the demo) | Extension 4 (binary labels) |
| Small dataset, avoid overfitting | Extension 5 (LoRA) |
| Logs in multiple languages | Extension 6 (XLM-RoBERTa) |
