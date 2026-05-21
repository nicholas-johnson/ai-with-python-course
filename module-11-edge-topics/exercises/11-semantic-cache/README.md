# Exercise 11 — Semantic Caching

## Recap

### The problem: redundant API calls

If 10 users ask "What is the capital of France?", "Capital of France?", and "What's France's capital?" — those are the same question phrased differently. Without caching, each one costs a full LLM API call (time + money). Traditional caching (exact string match) won't help because the strings are all different.

### The solution: match by meaning, not by text

**Semantic caching** embeds each query into a vector, then checks if any previously-cached query has a similar enough embedding. If the **cosine similarity** between the new query and a cached query is above a threshold (e.g. 0.95), it's "close enough" — return the cached response instead of calling the LLM again.

### What is cosine similarity?

Cosine similarity measures how similar the "direction" of two vectors is, on a scale from -1 (opposite) to 1 (identical). Two paraphrases of the same question will have cosine similarity around 0.95-0.99. Two unrelated questions will be around 0.3-0.6.

The formula:

```
cosine_similarity(a, b) = dot(a, b) / (|a| * |b|)
```

In Python:

```python
dot = sum(x * y for x, y in zip(a, b))
norm_a = math.sqrt(sum(x * x for x in a))
norm_b = math.sqrt(sum(x * x for x in b))
similarity = dot / (norm_a * norm_b)
```

### What is TTL?

**TTL** (Time To Live) means cache entries expire after a set time. If you cached an answer 24 hours ago, it might be stale. TTL ensures old entries are ignored.

### The cache flow

```
New query arrives
       │
       ▼
  Embed the query
       │
       ▼
  Compare against all cached embeddings (cosine similarity)
       │
       ├── Best match >= threshold (e.g. 0.95)?
       │         │
       │    YES: return cached response (cache HIT)
       │
       └── NO: call the LLM, store query + response in cache (cache MISS)
```

## What you build

A `cosine_similarity` function and a `SemanticCache` class in **`start.py`**:

| Item | What it does |
|---|---|
| `cosine_similarity(a, b)` | Compute cosine similarity between two embedding vectors |
| `SemanticCache.__init__(client, threshold)` | Set up the cache with an OpenAI client and similarity threshold |
| `SemanticCache.get(query)` | Look up a query — returns cached response or None |
| `SemanticCache.set(query, response)` | Store a query-response pair in the cache |

## Data format

The cache stores entries internally as a list of dicts:

```python
self.entries = [
    {
        "query": "What is the capital of France?",
        "embedding": [0.12, -0.45, 0.78, ...],  # 1536 floats
        "response": "The capital of France is Paris.",
        "timestamp": 1716300000.0,
    },
    ...
]
```

Usage:

```python
cache = SemanticCache(client, threshold=0.95)

# First query — cache miss, returns None
result = cache.get("What is France's capital?")  # None

# Store the response
cache.set("What is France's capital?", "The capital of France is Paris.")

# Paraphrased query — cache hit!
result = cache.get("Capital of France?")  # "The capital of France is Paris."
```

## Step-by-step

### 1. Implement `cosine_similarity`

```python
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

### 2. Implement `SemanticCache.__init__`

Store the client, threshold, and an empty list for cache entries:

```python
def __init__(self, client: OpenAI, threshold: float = 0.95):
    self.client = client
    self.threshold = threshold
    self.entries: list[dict] = []
```

### 3. Implement a helper `_embed` method

You'll need to embed queries for both `get` and `set`:

```python
def _embed(self, text: str) -> list[float]:
    response = self.client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
```

### 4. Implement `get`

Embed the query, compare against all cached embeddings, return the response if the best match exceeds the threshold:

```python
def get(self, query: str) -> str | None:
    if not self.entries:
        return None

    query_emb = self._embed(query)
    best_sim = -1.0
    best_response = None

    for entry in self.entries:
        sim = cosine_similarity(query_emb, entry["embedding"])
        if sim > best_sim:
            best_sim = sim
            best_response = entry["response"]

    if best_sim >= self.threshold:
        return best_response
    return None
```

### 5. Implement `set`

Embed the query and store everything:

```python
def set(self, query: str, response: str) -> None:
    embedding = self._embed(query)
    self.entries.append({
        "query": query,
        "embedding": embedding,
        "response": response,
        "timestamp": time.time(),
    })
```

> **Important:** The threshold value matters a lot. Too low (0.8) and unrelated queries will hit the cache. Too high (0.99) and even obvious paraphrases will miss. Start with 0.95 and adjust.

## Try it

```bash
cd module-11-edge-topics/exercises/11-semantic-cache
python start.py
```

Try asking the same question in different ways: "What is Python?", "Tell me about Python", "Explain Python to me". Check which ones hit the cache.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/11-semantic-cache/test_start.py -v
```

## Stretch Goals

- Add TTL (time-to-live) so old entries expire — skip entries where `time.time() - entry["timestamp"] > ttl_seconds`.
- Use a vector database (chromadb) as the cache backend for scalability.
- Add cache statistics (hit rate, miss rate, average similarity of hits).
