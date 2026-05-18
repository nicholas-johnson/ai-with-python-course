# Exercise 1: Build the Index

## Recap

RAG starts with an index. Before you can retrieve anything, you need to:

1. **Chunk** -- split documents into pieces small enough to be specific but large enough to be coherent (300-500 tokens is the sweet spot)
2. **Embed** -- convert each chunk into a dense vector using an embedding model
3. **Store** -- put the vectors into a searchable index

OpenAI's `text-embedding-3-small` converts text into 1536-dimensional vectors:

```python
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["some text to embed"],
)
vector = response.data[0].embedding  # list of 1536 floats
```

ChromaDB is an in-process vector database that handles storage and search:

```python
import chromadb

chroma = chromadb.Client()
collection = chroma.create_collection("my_docs")
collection.add(
    documents=["chunk text here"],
    metadatas=[{"source": "LOG-001"}],
    ids=["chunk_0"],
)

results = collection.query(query_texts=["search query"], n_results=5)
```

**Overlap** means consecutive chunks share some characters at the boundary, so concepts split across a boundary still appear complete in at least one chunk.

## What you build

A console app in **`start.py`** that loads scout logs, chunks them, embeds them into ChromaDB, and provides an interactive search REPL.

**Key functions:**

| Function | Description |
|---|---|
| `chunk_text(text, chunk_size, overlap)` | Split text into overlapping windows |
| `build_index(log_entries)` | Chunk all logs, embed, store in ChromaDB |
| `search(collection, query, k)` | Query the collection, return ranked results |

## Step-by-step

### 1. Load the scout logs

Load `data/scout_logs.json` from the project root. Each entry has `id`, `content`, `author`, `category`, and `tags`.

### 2. Implement `chunk_text`

Split a string into overlapping windows:

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

### 3. Build the index

For each log entry, chunk the content, then add all chunks to a ChromaDB collection with metadata (source ID, chunk index, author, category).

**Hint:** ChromaDB can embed for you if you pass `documents=`, but for this exercise use OpenAI embeddings explicitly so you understand the pipeline. You can batch embed all chunks at once.

### 4. Implement `search`

Use `collection.query(query_texts=[query], n_results=k)` to search. Format and return the results with distances and metadata.

### 5. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | Search the index, show top-k results |
| `/stats` | Show collection info (total chunks, sources) |
| `/chunk <id>` | Show full text + metadata of a specific chunk |
| `/similar <id>` | Find chunks similar to a given chunk |
| `quit` | Exit |

## Try it

```bash
cd module-05-rag-fundamentals/exercises/01-build-index
python start.py
```

Try searching for topics from the scout logs -- crew members, alien signals, first contact protocol, sensor readings.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `chunk_text` produces correct overlapping windows
- `build_index` creates a populated ChromaDB collection
- `search` returns ranked results with metadata

## Stretch goals

- Add sentence-aware chunking that splits on `.` boundaries instead of character count
- Try different chunk sizes and compare search quality
- Add a `/compare <size>` command that re-indexes with a different chunk size
