# Exercise 1 — AI Recipe Finder

Build a production-ready recipe search API that combines techniques from across the course into one FastAPI application.

## Techniques Used

| Technique | Module | File |
|---|---|---|
| OpenAI chat completions | Module 1 — Working with the LLM | `vision.py`, `rag.py` |
| Tool calling patterns | Module 2 — Tool Calling | `app.py` |
| RAG indexing & vector search | Module 5 — RAG Fundamentals | `rag.py` |
| Hybrid search (BM25 + vector) | Module 6 — RAG Optimisation | `rag.py` |
| LLM reranking | Module 6 — RAG Optimisation | `rag.py` |
| Semantic caching | Module 12 — Productionisation | `cache.py` |
| Structured tracing | Module 12 — Productionisation | `tracing.py` |
| Input/output guardrails | Module 12 — Productionisation | `guardrails.py` |
| Vision API | Module 1 — Working with the LLM | `vision.py` |

## Project Structure

```
01-recipe-finder/
├── data/
│   └── recipes.json          # Recipe dataset
├── starter/                   # Your working directory (has TODOs)
│   ├── app.py                 # FastAPI endpoints
│   ├── rag.py                 # RAG pipeline
│   ├── cache.py               # Semantic cache
│   ├── guardrails.py          # Safety checks
│   ├── vision.py              # Image analysis
│   ├── tracing.py             # Request tracing
│   └── config.py              # Environment config
├── solution/                  # Reference implementation
├── tests/
│   ├── conftest.py            # Test fixtures
│   └── test_app.py            # API tests
└── README.md
```

## Getting Started

### 1. Install dependencies

From the course root:

```bash
pip install fastapi uvicorn chromadb openai python-dotenv numpy
```

### 2. Set your API key

```bash
export OPENAI_API_KEY=your-key-here
```

### 3. Run the starter app

```bash
cd module-12-productionisation/exercises/01-recipe-finder
uvicorn starter.app:app --reload --port 8000
```

### 4. Run tests

```bash
pytest tests/ -v
```

## What to Implement

Work through the starter files in this order:

### Step 1: `rag.py` — Build the Search Pipeline
- **`build_index`**: Combine each recipe's title, description, and ingredients into a single text string. Embed in batches using `client.embeddings.create` and store in ChromaDB.
- **`_bm25_search`**: Get all documents from the collection, score each by counting matching query terms, return top k.
- **`_vector_search`**: Embed the query, call `collection.query`, return results as a list of dicts.
- **`hybrid_search`**: Run both searches, merge with Reciprocal Rank Fusion (RRF score = 1/(60 + rank + 1)).
- **`rerank`**: Format candidates for the LLM, ask it to return a JSON array of ranked numbers, reorder results.

### Step 2: `cache.py` — Add Semantic Caching
- **`get`**: Embed the query, compare against cached entries using cosine similarity. Return cached result if similarity >= threshold and entry hasn't expired.
- **`set`**: Embed the query, store with result and timestamp. Evict expired entries.

### Step 3: `guardrails.py` — Safety Checks
- **`check_allergens`**: Combine recipe text, check against user restrictions and common allergens list.
- **`redact_pii`**: Use regex to replace email addresses and phone numbers.

### Step 4: `vision.py` — Photo Search
- **`identify_ingredients`**: Send the base64 image to OpenAI's vision API with a system prompt asking for a comma-separated ingredient list.

### Step 5: `app.py` — Wire It All Together
- **`startup`**: Load `recipes.json` and call `build_index`.
- **`health`**: Return status and collection count.
- **`search`**: Check cache → hybrid search → dietary filter → rerank → format → cache result. Add tracing spans around each step.
- **`upload_photo`**: Identify ingredients → search → filter → rerank → format.
- **`get_recipe`**: Find recipe by ID, apply PII redaction.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check with index size |
| POST | `/api/search` | Search recipes by text query |
| POST | `/api/upload-photo` | Search by food photo |
| GET | `/api/recipe/{id}` | Get full recipe by ID |

### Example Search Request

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "quick vegetarian pasta", "dietary_filter": "vegetarian"}'
```
