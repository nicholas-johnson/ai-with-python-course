# Exercise 03 — HyDE (Hypothetical Document Embeddings)

## Recap

### The problem: query-document mismatch

When you embed a short question like *"What causes warp core instability?"*, it lands in a very different part of embedding space than a detailed paragraph explaining the causes. Questions are short and interrogative; documents are long and declarative. Their embeddings end up far apart even when they're about the same topic.

### The solution: search with a fake answer

**HyDE** (Hypothetical Document Embeddings) works around this by generating a **hypothetical answer** first, then searching with *that* instead of the original question:

1. Ask the LLM: "Write a paragraph that answers this question" (the answer doesn't need to be factually correct — it just needs to *look like* a real document).
2. Embed the hypothetical answer.
3. Search your vector store using that embedding.

Because the hypothetical answer is structurally similar to real documents (same vocabulary, same level of detail, same declarative tone), its embedding lands much closer to relevant real documents than the original question would.

### What the flow looks like

```
Question: "What causes warp core instability?"
         │
         ▼
   Generate hypothetical answer (LLM call)
         │
         ▼
"Warp core instability is primarily caused by dilithium crystal
 degradation, plasma injection asymmetry, and magnetic containment
 fluctuations. When the crystal matrix fragments..."
         │
         ▼
   Embed this paragraph (embeddings API)
         │
         ▼
   Search vector store with that embedding
         │
         ▼
   Return real documents that are nearby
```

### The generation prompt

The key insight is telling the LLM it doesn't need to be correct — just realistic:

```python
prompt = (
    "Write a short, detailed paragraph that answers this question. "
    "It does not need to be factually correct — just write what a "
    "good answer would look like in terms of structure, vocabulary, "
    "and level of detail.\n\n"
    f"Question: {query}"
)
```

## What you build

Three functions in **`start.py`** that form the HyDE pipeline:

| Function | What it does |
|---|---|
| `generate_hypothetical_document(client, query)` | Ask the LLM to write a fake but realistic answer paragraph |
| `embed_text(client, text)` | Convert text to an embedding vector using OpenAI's API |
| `hyde_search(client, query, collection)` | Full pipeline: generate → embed → search |

## Data format

The `collection` parameter is a ChromaDB collection. You search it like this:

```python
results = collection.query(
    query_embeddings=[embedding],  # list containing one embedding vector
    n_results=5,
)
# results["documents"] = [["doc text 1", "doc text 2", ...]]
# results["distances"] = [[0.12, 0.23, ...]]
```

The return value of `hyde_search` is a dict:

```python
{
    "hypothetical_document": "Warp core instability is primarily caused by...",
    "results": {
        "documents": [["Real doc 1...", "Real doc 2..."]],
        "distances": [[0.15, 0.28]],
    },
}
```

## Step-by-step

### 1. Implement `generate_hypothetical_document`

Use `client.chat.completions.create` with `gpt-4o-mini`. Use a `temperature` of 0.7 (we want some creativity, not a deterministic answer). Return the text content of the response.

> **Important:** The prompt should explicitly say the answer doesn't need to be factually correct. This frees the model to write something structurally realistic rather than hedging.

### 2. Implement `embed_text`

Call the OpenAI embeddings API:

```python
def embed_text(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
```

### 3. Implement `hyde_search`

Chain the two functions together, then query the collection:

```python
def hyde_search(client, query, collection, n_results=5):
    hypothetical_doc = generate_hypothetical_document(client, query)
    embedding = embed_text(client, hypothetical_doc)
    results = collection.query(query_embeddings=[embedding], n_results=n_results)
    return {"hypothetical_document": hypothetical_doc, "results": results}
```

## Try it

```bash
cd module-11-edge-topics/exercises/03-hyde
python start.py
```

Try questions where the wording is very different from how a document would phrase it: "Why do engines fail?", "How do you fix broken sensors?", "What's the crew supposed to do in an emergency?"

## Running Tests

```bash
pytest module-11-edge-topics/exercises/03-hyde/test_start.py -v
```

## Stretch Goals

- Average the original query embedding with the HyDE embedding (gives you the best of both).
- Generate multiple hypothetical documents and average their embeddings.
- Compare retrieval quality with and without HyDE on sample queries.
