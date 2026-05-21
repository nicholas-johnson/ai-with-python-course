# Module 12 — Capstone Ideas

The exercises in this folder (`01-recipe-finder` through `04-personal-assistant`) are full-stack projects with starter code, tests, and reference solutions. The ideas below are **open-ended capstone projects** — no starter code, no tests, just a title and enough detail to get you building.

They focus on **Hugging Face models running on CPU**, so you can work offline after the first download and avoid API costs. You bring your own project structure, dataset, and frontend (if any).

## Prerequisites

```bash
pip install -e ".[local-ml]"
```

For model sizes and CPU tips, see [Exercise 15 — Hugging Face Run](../../module-11-edge-topics/exercises/15-huggingface-run/README.md) in Module 11.

---

## Exercise 05 — Sentiment Monitor

Build a service that ingests text (reviews, support tickets, ship logs, social posts) and tracks sentiment over time. Expose a FastAPI API that classifies each message, stores results, and returns rolling aggregates (e.g. positive ratio in the last hour).

**What to build**

- Load a sequence-classification model and run batch inference on incoming text
- Persist classifications with timestamps (SQLite or JSON lines is fine)
- Endpoints: classify one message, classify a batch, get summary stats for a time window
- Add request tracing so you can see latency per classification batch

**Suggested models**

| Model                                              | Task              | Size   |
| -------------------------------------------------- | ----------------- | ------ |
| `distilbert-base-uncased-finetuned-sst-2-english`  | Binary sentiment  | ~250MB |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | 3-class sentiment | ~500MB |

**Techniques → Course modules**

| Technique                                                            | Course module                 |
| -------------------------------------------------------------------- | ----------------------------- |
| HF inference (`AutoTokenizer`, `AutoModelForSequenceClassification`) | Module 11 — Edge Topics       |
| FastAPI endpoints                                                    | Exercises 01–04               |
| Tracing / observability                                              | Module 12 — Productionisation |

---

## Exercise 06 — Multilingual FAQ Bot

Build a Q&A system that accepts questions in multiple languages. Translate the question to English with a local translation model, run your RAG pipeline against an English knowledge base, then translate the answer back to the user's language.

**What to build**

- A document index (ChromaDB or similar) over English FAQ or product docs
- Detect or accept a source language code on each request
- Pipeline: translate in → retrieve + generate answer in English → translate out
- Guardrails on max input length and empty retrieval results

**Suggested models**

| Model                        | Direction        | Size   |
| ---------------------------- | ---------------- | ------ |
| `Helsinki-NLP/opus-mt-en-fr` | English → French | ~300MB |
| `Helsinki-NLP/opus-mt-fr-en` | French → English | ~300MB |
| `Helsinki-NLP/opus-mt-en-de` | English → German | ~300MB |

Pick language pairs you care about; each pair is a separate model download.

**Techniques → Course modules**

| Technique                             | Course module               |
| ------------------------------------- | --------------------------- |
| Translation (`AutoModelForSeq2SeqLM`) | Module 11 — Edge Topics     |
| RAG (index, search, answer)           | Module 5 — RAG Fundamentals |
| Guardrails                            | Module 8 — Guardrails       |

---

## Exercise 07 — Content Moderation Pipeline

Create a moderation service that scores user input through several small classifiers before any downstream LLM or storage step. Block, flag, or allow content based on combined scores and configurable thresholds.

**What to build**

- Multiple HF classifiers (e.g. toxicity, hate, sexual content) run on the same text
- A single `/moderate` endpoint returning per-label scores and an overall decision
- Guardrails that reject requests over a character limit or with too many URLs
- Optional: log flagged samples for human review (redact PII in logs)

**Suggested models**

| Model                      | Task                            | Size   |
| -------------------------- | ------------------------------- | ------ |
| `unitary/toxic-bert`       | Toxic comment detection         | ~440MB |
| `facebook/bart-large-mnli` | Zero-shot topic / policy labels | ~1.6GB |

Start with one toxicity model; add zero-shot labels only if you need custom categories without training data.

**Techniques → Course modules**

| Technique                 | Course module                 |
| ------------------------- | ----------------------------- |
| HF classification         | Module 11 — Edge Topics       |
| Guardrails & policy gates | Module 8 — Guardrails         |
| Tracing                   | Module 12 — Productionisation |

---

## Exercise 08 — Local Embedding Search

Replace OpenAI embeddings with a sentence-transformer model and build a **fully offline** RAG pipeline: index documents, search by semantic similarity, and optionally rerank with a small local model or heuristics — no API keys required.

**What to build**

- Embed your corpus with `sentence-transformers` (or `AutoModel` + mean pooling)
- Store vectors in ChromaDB (or numpy + cosine similarity for a small corpus)
- Search endpoint that returns top-k chunks with scores
- Optional: hybrid search (BM25 + vectors) if you want to combine with Module 11 patterns

**Suggested models**

| Model                                     | Task                      | Size   |
| ----------------------------------------- | ------------------------- | ------ |
| `sentence-transformers/all-MiniLM-L6-v2`  | 384-dim embeddings        | ~90MB  |
| `sentence-transformers/all-mpnet-base-v2` | Higher-quality embeddings | ~420MB |

**Techniques → Course modules**

| Technique                   | Course module                 |
| --------------------------- | ----------------------------- |
| Embeddings & vector search  | Module 5 — RAG Fundamentals   |
| Hybrid search (optional)    | Module 11 — Edge Topics       |
| Semantic caching (optional) | Module 12 — Productionisation |

---

## Exercise 09 — Document Classifier API

Fine-tune DistilBERT on a custom labeled dataset, save the checkpoint, and deploy it behind FastAPI with production patterns: health checks, semantic caching for repeated queries, and tracing.

**What to build**

- Labeled JSON dataset (text + category), similar to Module 11 Exercise 14
- Train with Hugging Face `Trainer` on CPU (keep `max_steps` modest for a laptop)
- `/classify` endpoint loading your saved model from disk
- Cache identical or near-identical queries; trace train vs inference paths separately

**Suggested models**

| Model                     | Task                 | Size   |
| ------------------------- | -------------------- | ------ |
| `distilbert-base-uncased` | Base for fine-tuning | ~250MB |

**Techniques → Course modules**

| Technique                             | Course module                 |
| ------------------------------------- | ----------------------------- |
| Fine-tuning (`Trainer`, labeled data) | Module 11 — Exercise 14       |
| FastAPI deployment                    | Exercises 01–04               |
| Semantic caching, tracing             | Module 12 — Productionisation |

---

## Exercise 10 — Summarisation Service

Build a service that accepts long text (articles, meeting notes, incident reports) and returns a short summary. Enforce input length limits, validate output shape (e.g. bullet list or fixed fields), and handle timeouts gracefully on CPU.

**What to build**

- `/summarise` accepting plain text or a URL-fetched document (your choice)
- Truncate or chunk input that exceeds the model's context window
- Structured response: e.g. `{"summary": "...", "bullet_points": ["...", "..."]}`
- Guardrails: max tokens in, min/max length out, reject empty input

**Suggested models**

| Model                     | Task                            | Size   |
| ------------------------- | ------------------------------- | ------ |
| `google/flan-t5-small`    | Instruction-style summarisation | ~300MB |
| `facebook/bart-large-cnn` | Abstractive summarisation       | ~1.6GB |

`flan-t5-small` is lighter on CPU; `bart-large-cnn` is stronger but slower.

**Techniques → Course modules**

| Technique                   | Course module                 |
| --------------------------- | ----------------------------- |
| Seq2seq generation          | Module 11 — Edge Topics       |
| Prompt / output structuring | Module 7 — Prompt Engineering |
| Guardrails                  | Module 8 — Guardrails         |

---

## Exercise 11 — Zero-Shot Classifier

Build a labeling API that classifies text into **arbitrary categories supplied at request time** — no training step. Useful for triage, routing, or tagging when categories change often.

**What to build**

- `/classify` with body: `{"text": "...", "labels": ["billing", "technical", "other"]}`
- Return scores per label and the winning label
- Cache results keyed on text + sorted label list
- Document latency expectations (MNli models are heavier than DistilBERT)

**Suggested models**

| Model                                   | Task                     | Size   |
| --------------------------------------- | ------------------------ | ------ |
| `facebook/bart-large-mnli`              | Zero-shot NLI            | ~1.6GB |
| `typeform/distilbert-base-uncased-mnli` | Smaller zero-shot option | ~250MB |

**Techniques → Course modules**

| Technique                | Course module                 |
| ------------------------ | ----------------------------- |
| Zero-shot classification | Module 11 — Edge Topics       |
| Semantic caching         | Module 12 — Productionisation |
| FastAPI                  | Exercises 01–04               |

---

## Exercise 12 — Local Chatbot with Memory

Deploy a small instruction-tuned causal language model behind an API with multi-turn conversation memory, token budgets, and reliability patterns from this module (circuit breaker, cost/token limits).

**What to build**

- Chat endpoint with `session_id`; store recent turns server-side
- Trim history to fit context window (drop oldest messages first)
- Cap `max_new_tokens` per request; return token usage in the response
- Circuit breaker: if inference fails repeatedly, return a friendly fallback without retry storms
- Optional: stream tokens with SSE (see Exercise 04 for patterns)

**Suggested models**

| Model                                 | Task                         | Size   |
| ------------------------------------- | ---------------------------- | ------ |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | Chat / instructions          | ~720MB |
| `Qwen/Qwen2-0.5B-Instruct`            | Alternative small chat model | ~1GB   |

See Module 11 demo `17_huggingface_generate.py` for a minimal local chat loop.

**Techniques → Course modules**

| Technique                      | Course module                    |
| ------------------------------ | -------------------------------- |
| Causal LM generation           | Module 11 — Edge Topics          |
| Conversation memory            | Module 4 — Agents                |
| Circuit breaker, cost controls | Module 12 — Productionisation    |
| SSE streaming (optional)       | Exercise 04 — Personal Assistant |

---

## Tips for all capstones

- **First run downloads models** — plan for hundreds of MB to ~1.6GB per model; reuse the same `model_id` across restarts.
- **Always use `model.eval()` and `torch.no_grad()`** for inference.
- **Borrow production patterns** from exercises 01–04: `tracing.py`-style spans, semantic cache, guardrails on inputs and outputs.
- **No starter code means you design the layout** — a single `app.py` is fine for a weekend project; split into modules when complexity grows.
- Browse more models at [huggingface.co/models](https://huggingface.co/models); prefer names with `distil`, `small`, `mini`, or parameter counts under ~500M for comfortable CPU use.
