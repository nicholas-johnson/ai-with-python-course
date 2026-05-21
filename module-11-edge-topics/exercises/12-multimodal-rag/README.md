# Exercise 12 — Multimodal RAG

## Recap

### The problem: knowledge bases aren't just text

Real-world document collections include images — diagrams, photos, charts, screenshots. Standard RAG only handles text, so images get ignored entirely during retrieval.

### The solution: describe images, then embed the descriptions

**Multimodal RAG** extends your search index to handle images by:

1. Sending each image to a **vision model** (like GPT-4o-mini, which can "see" images) and getting back a text description.
2. Embedding that text description into a vector — just like you'd embed a text chunk.
3. Storing everything in the same index. Now text queries can match images (via their descriptions) and vice versa.

### How vision models work with images

You send an image to GPT-4o-mini by base64-encoding it and including it in the message content:

```python
import base64

with open("diagram.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image in detail."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
        ],
    }],
)
description = response.choices[0].message.content
```

The model responds with a text description like: "A schematic diagram showing the reactor cooling system with three primary loops connected to heat exchangers..."

### What base64 encoding is

**Base64** is a way to represent binary data (like image bytes) as a text string. It's needed because JSON messages can only contain text, not raw bytes. Python's `base64.b64encode()` converts bytes to a base64 string.

## What you build

Five functions in **`start.py`**:

| Function | What it does |
|---|---|
| `describe_image(client, image_path)` | Send an image to the vision model, get a text description |
| `embed_text(client, text)` | Convert text to an embedding vector |
| `index_item(client, item)` | Create an index entry for either a text chunk or an image |
| `build_multimodal_index(client, items)` | Index a mixed collection of text and images |
| `search_index(client, query, index)` | Search the unified index with a text query |

## Data format

Input items can be text or images:

```python
items = [
    {"id": "doc-1", "type": "text", "content": "The reactor operates at 3500K..."},
    {"id": "doc-2", "type": "text", "content": "Cooling systems use three loops..."},
    {"id": "img-1", "type": "image", "path": "data/reactor_diagram.png", "id": "img-1"},
]
```

After indexing, each item becomes an entry with an embedding:

```python
{
    "id": "img-1",
    "type": "image",
    "text": "A schematic diagram showing the reactor cooling system...",  # generated description
    "embedding": [0.12, -0.45, ...],   # 1536 floats
    "source": "data/reactor_diagram.png",
}
```

Search results include a similarity score:

```python
[
    {"id": "img-1", "type": "image", "text": "A schematic...", "score": 0.89, ...},
    {"id": "doc-1", "type": "text", "text": "The reactor operates...", "score": 0.85, ...},
]
```

## Step-by-step

### 1. Implement `describe_image`

Read the image file, base64-encode it, send to GPT-4o-mini with a descriptive prompt:

```python
def describe_image(client: OpenAI, image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in detail for a search index. "
                            "Include all visible objects, text, colors, and layout.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"},
                },
            ],
        }],
    )
    return response.choices[0].message.content
```

> **Important:** The description prompt matters. Ask for search-relevant details (objects, text, colors, layout) rather than artistic interpretation.

### 2. Implement `embed_text`

```python
def embed_text(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding
```

### 3. Implement `index_item`

Handle both text and image items. For images, describe first, then embed the description:

```python
def index_item(client: OpenAI, item: dict) -> dict:
    if item["type"] == "text":
        text = item["content"]
        source = ""
    elif item["type"] == "image":
        text = describe_image(client, item["path"])
        source = item["path"]
    else:
        raise ValueError(f"Unknown item type: {item['type']}")

    embedding = embed_text(client, text)
    return {"id": item["id"], "type": item["type"], "text": text, "embedding": embedding, "source": source}
```

### 4. Implement `build_multimodal_index`

Just map `index_item` over all items:

```python
def build_multimodal_index(client, items):
    return [index_item(client, item) for item in items]
```

### 5. Implement `search_index`

Embed the query, compute cosine similarity against each index entry, sort descending:

```python
def search_index(client, query, index, top_k=5):
    query_emb = embed_text(client, query)
    scored = []
    for entry in index:
        sim = cosine_similarity(query_emb, entry["embedding"])
        scored.append({**entry, "score": sim})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
```

## Try it

```bash
cd module-11-edge-topics/exercises/12-multimodal-rag
python start.py
```

Try queries that might match images: "reactor diagram", "cooling system schematic", "crew photo".

## Running Tests

```bash
pytest module-11-edge-topics/exercises/12-multimodal-rag/test_start.py -v
```

## Stretch Goals

- Pass actual images to the generation step for richer answers (not just the description).
- Add metadata filtering (search only images, or only text).
- Implement cross-modal queries (text query returning image results, with the image path displayed).
