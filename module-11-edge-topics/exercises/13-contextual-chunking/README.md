# Exercise 13 — Contextual Chunking

## Recap

### Why chunking matters

Before you can search documents, you have to split them into smaller pieces (chunks). The way you split them has a huge impact on retrieval quality:

- **Too big** (whole documents) — the embedding becomes a vague average of many topics, losing precision.
- **Too small** (single sentences) — you lose surrounding context needed to understand the sentence.
- **Bad boundaries** — if you split mid-sentence or mid-paragraph, important information gets torn apart.

### Three chunking strategies

This exercise implements three approaches, from simple to sophisticated:

**1. Fixed-size chunks** — split text into chunks of N words. Simple but can split mid-thought:

```
[words 0-99] [words 100-199] [words 200-299]
```

**2. Overlapping chunks** — like fixed-size, but consecutive chunks share some words at the boundary. This means any concept that falls on a boundary still appears complete in at least one chunk:

```
[words 0-99] [words 80-179] [words 160-259]
          ^^^^overlap^^^^  ^^^^overlap^^^^
```

**3. Parent-child chunks** — use *small* chunks for precise search matching, but return the *larger* parent chunk for generation context. You search the children (focused) but read the parent (complete):

```
Parent chunk (200 words): "The reactor system comprises three subsystems..."
  ├── Child 1 (50 words): "The reactor system comprises..."
  ├── Child 2 (50 words): "The cooling loop uses..."
  ├── Child 3 (50 words): "Emergency shutdown procedures..."
  └── Child 4 (50 words): "Maintenance schedules require..."
```

When a search matches Child 3, you return the full Parent chunk — giving the LLM enough context to generate a good answer.

### Why parent-child works best

Small chunks give better search precision (a 50-word chunk about "emergency shutdown" matches that query better than a 200-word chunk that also mentions cooling and maintenance). But when you pass results to the LLM, you want more context. Parent-child gives you both: precise matching + rich context.

## What you build

Four functions in **`start.py`**:

| Function | What it does |
|---|---|
| `fixed_chunk(text, chunk_size)` | Split text into fixed-size word chunks |
| `overlap_chunk(text, chunk_size, overlap)` | Split with overlapping windows |
| `parent_child_chunk(text, parent_size, child_size)` | Two-level parent/child chunking |
| `retrieve_with_context(query_embedding, child_chunks, top_k)` | Search children, return parent chunks |

## Data format

Input — a long text string:

```python
text = "The reactor system comprises three subsystems. The primary cooling loop..."
# (imagine hundreds of words)
```

`fixed_chunk` and `overlap_chunk` return lists of strings:

```python
["The reactor system comprises...", "The cooling loop uses...", ...]
```

`parent_child_chunk` returns a list of dicts linking children to parents:

```python
[
    {"child_text": "The reactor system comprises...", "parent_id": 0, "parent_text": "The reactor system...loop...shutdown..."},
    {"child_text": "The cooling loop uses...", "parent_id": 0, "parent_text": "The reactor system...loop...shutdown..."},
    {"child_text": "Navigation uses stellar...", "parent_id": 1, "parent_text": "Navigation uses...course...sensors..."},
]
```

`retrieve_with_context` returns unique parent chunks ranked by how well their best child matched:

```python
[
    {"parent_id": 0, "parent_text": "The reactor system...", "best_child_score": 0.92},
    {"parent_id": 1, "parent_text": "Navigation uses...", "best_child_score": 0.71},
]
```

## Step-by-step

### 1. Implement `fixed_chunk`

Split text into words, then group into chunks of `chunk_size` words:

```python
def fixed_chunk(text: str, chunk_size: int = 100) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks
```

### 2. Implement `overlap_chunk`

Like fixed_chunk, but advance by `chunk_size - overlap` words each step instead of `chunk_size`:

```python
def overlap_chunk(text: str, chunk_size: int = 100, overlap: int = 20) -> list[str]:
    words = text.split()
    chunks = []
    stride = chunk_size - overlap
    for i in range(0, len(words), stride):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks
```

> **Important:** Guard against `overlap >= chunk_size`, which would make `stride` zero or negative and cause an infinite loop. If that happens, set stride to 1.

### 3. Implement `parent_child_chunk`

First split into parent-sized chunks, then split each parent into child-sized chunks. Track which parent each child belongs to:

```python
def parent_child_chunk(text: str, parent_size: int = 200, child_size: int = 50) -> list[dict]:
    words = text.split()
    chunks = []
    parent_id = 0

    for parent_start in range(0, len(words), parent_size):
        parent_words = words[parent_start:parent_start + parent_size]
        parent_text = " ".join(parent_words)

        for child_start in range(0, len(parent_words), child_size):
            child_text = " ".join(parent_words[child_start:child_start + child_size])
            if child_text.strip():
                chunks.append({
                    "child_text": child_text,
                    "parent_id": parent_id,
                    "parent_text": parent_text,
                })
        parent_id += 1

    return chunks
```

### 4. Implement `retrieve_with_context`

Search across child chunks (by embedding similarity), but deduplicate by parent — only keep the best-scoring child per parent, then return the top-k parents:

```python
def retrieve_with_context(query_embedding, child_chunks, top_k=3):
    parent_scores = {}

    for child in child_chunks:
        sim = cosine_similarity(query_embedding, child["embedding"])
        pid = child["parent_id"]

        if pid not in parent_scores or sim > parent_scores[pid]["best_child_score"]:
            parent_scores[pid] = {
                "parent_id": pid,
                "parent_text": child["parent_text"],
                "best_child_score": sim,
            }

    ranked = sorted(parent_scores.values(), key=lambda x: x["best_child_score"], reverse=True)
    return ranked[:top_k]
```

> **Important:** Each child chunk needs an `"embedding"` field for this to work. You'll need to embed the child texts before calling `retrieve_with_context`. The test may provide pre-computed embeddings.

## Try it

```bash
cd module-11-edge-topics/exercises/13-contextual-chunking
python start.py
```

Try chunking a long document with different sizes and see how many chunks you get. Compare search results from fixed vs. overlap vs. parent-child.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/13-contextual-chunking/test_start.py -v
```

## Stretch Goals

- Implement semantic chunking using sentence-level similarity drop-off (split where the topic changes).
- Compare retrieval quality across different chunking strategies on the same query set.
- Add metadata tracking (chunk position, word count, parent-child relationships).
