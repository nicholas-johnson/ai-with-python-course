# Exercise 02 — Re-ranking

## Recap

When you search a large collection, you need the first step (retrieval) to be fast. It scans thousands of documents in milliseconds using a quick comparison (embedding dot-product). The trade-off is that this fast comparison sometimes gets the ranking wrong — it might put a so-so result at position 2 and a perfect result at position 8.

**Re-ranking** fixes this with a two-stage pipeline:

1. **Stage 1 — Retrieve broadly:** Pull back 20-50 candidates using fast vector search (high recall, imperfect precision).
2. **Stage 2 — Re-rank precisely:** Score each candidate against the query using a more expensive method, then keep only the top 5.

### Why the second pass is more accurate

In Stage 1, the query and each document are embedded *separately* — the model never sees them together. In Stage 2, a **cross-encoder** (or in our case, an LLM) sees the query and passage *side by side* and judges relevance directly. This joint comparison is much more accurate, but too slow to run on thousands of documents — that's why you only run it on the shortlist from Stage 1.

### What the scoring looks like

We use the LLM as a relevance scorer. The prompt is simple:

```
Rate how relevant this passage is to the query on a scale of 0 to 10.
Respond with ONLY a number.

Query: What safety protocols exist for reactor maintenance?

Passage: During reactor maintenance, all personnel must wear Class-B
radiation suits and maintain a minimum distance of 3 metres from the
core housing unless actively performing calibration work.
```

The LLM responds with a single number like `9`. You do this for each candidate passage, then sort by score.

## What you build

Three functions in **`start.py`** that form a two-stage retrieval pipeline:

| Function | What it does |
|---|---|
| `score_relevance(client, query, passage)` | Ask the LLM to score one passage (0-10) |
| `rerank(client, query, passages, top_k)` | Score all passages, sort by score, return top-k |
| `two_stage_retrieve(client, query, retrieve_fn, retrieve_k, final_k)` | Full pipeline: retrieve broadly, then re-rank |

## Data format

Each passage is a dict with at least a `"text"` key:

```python
passages = [
    {"text": "Reactor maintenance requires Class-B suits...", "id": "DOC-042"},
    {"text": "Crew meal schedules are posted weekly...", "id": "DOC-108"},
    {"text": "Core temperature monitoring runs every 30s...", "id": "DOC-019"},
]
```

After re-ranking, each passage gets a `"rerank_score"` added:

```python
[
    {"text": "Reactor maintenance requires...", "id": "DOC-042", "rerank_score": 9.0},
    {"text": "Core temperature monitoring...", "id": "DOC-019", "rerank_score": 7.0},
]
```

## Step-by-step

### 1. Implement `score_relevance`

Use `client.chat.completions.create` with a prompt that asks the LLM to rate relevance from 0 to 10. Return the number as a float.

```python
def score_relevance(client: OpenAI, query: str, passage: str) -> float:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Rate how relevant this passage is to the query on a scale "
                f"of 0 to 10. Respond with ONLY a number.\n\n"
                f"Query: {query}\n\n"
                f"Passage: {passage}"
            ),
        }],
        temperature=0,
    )
    # Parse the response — it should be just a number
    ...
```

> **Important:** Wrap the `float()` conversion in a try/except. If the LLM returns something unexpected (like "8/10"), default to 0.0 rather than crashing.

### 2. Implement `rerank`

Loop through each passage, call `score_relevance`, attach the score, sort descending, and slice to `top_k`:

```python
scored = []
for passage in passages:
    score = score_relevance(client, query, passage["text"])
    scored.append({**passage, "rerank_score": score})
scored.sort(key=lambda x: x["rerank_score"], reverse=True)
return scored[:top_k]
```

### 3. Implement `two_stage_retrieve`

This wires it all together. Call the provided `retrieve_fn` to get initial candidates, then pass them to `rerank`:

```python
def two_stage_retrieve(client, query, retrieve_fn, retrieve_k=20, final_k=5):
    candidates = retrieve_fn(query, retrieve_k)
    return rerank(client, query, candidates, top_k=final_k)
```

## Try it

```bash
cd module-11-edge-topics/exercises/02-reranking
python start.py
```

## Running Tests

```bash
pytest module-11-edge-topics/exercises/02-reranking/test_start.py -v
```

## Stretch Goals

- Batch multiple passages into a single LLM call for efficiency (send all passages at once, ask for a JSON array of scores).
- Compare LLM re-ranking quality against a simple keyword-overlap scorer.
- Add caching so repeated (query, passage) pairs are not re-scored.
