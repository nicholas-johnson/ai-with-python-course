# Exercise 01 — Hybrid Search

## Recap

When you search for documents, there are two main approaches:

- **Keyword search (BM25)** — looks for documents that contain the same words as your query. If you search for "reactor temperature", it finds documents with those exact words. BM25 is just a scoring formula that counts how often your search words appear in each document, while penalising words that appear everywhere (like "the" or "is").

- **Vector (semantic) search** — converts your query into a list of numbers (an "embedding") and finds documents whose embeddings are nearby in mathematical space. This catches synonyms and related concepts — "reactor temperature" might match a document about "core thermal readings" even though they share no words.

Each approach misses things the other catches. Hybrid search runs **both** in parallel and merges the results using a formula called **Reciprocal Rank Fusion (RRF)**.

### How RRF works

Each search method returns a ranked list of documents (best first). RRF doesn't care about the raw scores — it only uses the **rank position**. For each document, it sums up:

```
RRF_score(doc) = 1/(k + rank_in_list_1) + 1/(k + rank_in_list_2)
```

`k` is a constant (usually 60) that prevents the top-ranked result from dominating. A document ranked #1 in both lists gets `1/61 + 1/61 = 0.033`. A document ranked #1 in one and #5 in the other gets `1/61 + 1/65 = 0.032`. They end up close together — that's the point.

### What BM25 scoring looks like in code

```python
query_tokens = "reactor temperature".lower().split()  # ["reactor", "temperature"]

for doc in documents:
    doc_tokens = doc["text"].lower().split()
    for query_word in query_tokens:
        tf = doc_tokens.count(query_word)         # how many times the word appears in this doc
        idf = math.log((N + 1) / (docs_with_word + 1))  # rarer words score higher
        score += tf * idf
```

**TF** (term frequency) = how often a word appears in a document. **IDF** (inverse document frequency) = a bonus for rare words. If "temperature" appears in 2 of 100 documents, it's more useful than "the" which appears in all 100.

## What you build

A set of functions in **`start.py`** that implement a complete hybrid search pipeline — no external dependencies needed (pure Python + `math`).

| Function | What it does |
|---|---|
| `tokenize(text)` | Lowercase and split text into word tokens |
| `bm25_search(query, documents)` | Score and rank documents by keyword overlap |
| `reciprocal_rank_fusion(ranked_lists, k)` | Merge multiple ranked lists using RRF |
| `_cosine_similarity(a, b)` | Compute cosine similarity between two number lists |
| `vector_search(query_embedding, document_embeddings)` | Rank documents by embedding similarity |
| `hybrid_search(query, documents, query_embedding, document_embeddings)` | Run both searches and fuse with RRF |

## Data format

Your documents look like this:

```python
documents = [
    {"id": "LOG-001", "text": "Reactor temperature holding steady at 3500K..."},
    {"id": "LOG-002", "text": "Navigation array recalibrated after asteroid field..."},
    {"id": "LOG-003", "text": "Core thermal readings exceeded safety threshold..."},
]
```

Your embeddings are pre-computed (a dict mapping doc ID to a list of floats):

```python
document_embeddings = {
    "LOG-001": [0.12, -0.45, 0.78, ...],  # 1536 numbers from OpenAI
    "LOG-002": [0.34, 0.11, -0.22, ...],
    "LOG-003": [0.15, -0.41, 0.80, ...],
}
query_embedding = [0.13, -0.44, 0.77, ...]
```

The final output of `hybrid_search` is a list of `(doc_id, rrf_score)` tuples:

```python
[("LOG-001", 0.0328), ("LOG-003", 0.0311), ("LOG-002", 0.0164)]
```

## Step-by-step

### 1. Implement `tokenize`

The simplest possible tokeniser — lowercase the text, then split on whitespace:

```python
def tokenize(text: str) -> list[str]:
    return text.lower().split()
```

### 2. Implement `bm25_search`

This is the trickiest function. Work through it in order:

1. Tokenize the query.
2. Count document frequency (df) — for each unique word, how many documents contain it?
3. For each document, score it: loop through query tokens, compute `TF * IDF` for each.
4. Sort by score descending, return the top-k doc IDs.

**Hint** — computing document frequency:

```python
df: dict[str, int] = {}
for doc in documents:
    unique_tokens = set(tokenize(doc["text"]))
    for token in unique_tokens:
        df[token] = df.get(token, 0) + 1
```

**Hint** — IDF formula: `math.log((n + 1) / (df.get(token, 0) + 1))` where `n` is the total number of documents.

### 3. Implement `_cosine_similarity`

Cosine similarity measures how similar the "direction" of two vectors is (ignoring length). The formula is:

```
dot(a, b) / (magnitude(a) * magnitude(b))
```

In Python:

```python
dot = sum(x * y for x, y in zip(a, b))
norm_a = math.sqrt(sum(x * x for x in a))
norm_b = math.sqrt(sum(x * x for x in b))
```

> **Important:** Handle the case where either norm is 0 (return 0.0) to avoid division by zero.

### 4. Implement `vector_search`

Loop through all document embeddings, compute cosine similarity with the query embedding, sort descending, return the top-k IDs.

### 5. Implement `reciprocal_rank_fusion`

For each ranked list, loop through with `enumerate(..., start=1)` to get 1-based ranks. Accumulate `1/(k + rank)` for each doc ID across all lists.

```python
scores: dict[str, float] = {}
for ranked_list in ranked_lists:
    for rank, doc_id in enumerate(ranked_list, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
```

### 6. Implement `hybrid_search`

Call `bm25_search` and `vector_search`, then pass both ranked lists to `reciprocal_rank_fusion`. Return the top-k fused results.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/01-hybrid-search/test_start.py -v
```

## Stretch Goals

- Add TF-IDF weighting instead of raw term frequency.
- Experiment with different `k` values and observe how it affects fusion.
- Add a weight parameter to bias toward vector or keyword results.
