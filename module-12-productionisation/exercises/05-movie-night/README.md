# Exercise 05 — AI Movie Night

A full-stack AI movie recommendation app combining **RAG** (mood-based search) with **text-to-SQL** (data questions), wrapped in production patterns.

## Techniques → Course Modules

| Technique Used | Where in This Exercise | Course Module |
| --- | --- | --- |
| OpenAI Responses API | `rag.py` reranking, `sql.py` generation | Module 1 — Working with the LLM |
| Tool calling (structured output) | `sql.py` text-to-SQL | Module 2 — Tool Calling |
| Embeddings & vector search | `rag.py` ChromaDB index + search | Module 5 — RAG Fundamentals |
| RAG pipeline | `rag.py` build → search → rerank | Module 5 — RAG Fundamentals |
| Prompt engineering | System prompts in `rag.py`, `sql.py` | Module 4 — GenAI Strategies |
| Guardrails & safety | `guardrails.py` SQL validation | Module 13 — Edge Topics |
| Semantic caching | `cache.py` cosine similarity cache | Module 13 — Edge Topics |
| Tracing / observability | `tracing.py` span-based tracing | Module 12 — Productionisation |

## Project Structure

```
05-movie-night/
├── data/
│   └── movies.json          # Movie dataset (100 films)
├── starter/                  # Your working copy (has TODOs)
│   ├── app.py                # FastAPI endpoints
│   ├── rag.py                # RAG pipeline
│   ├── sql.py                # Text-to-SQL pipeline
│   ├── guardrails.py         # SQL safety checks
│   ├── cache.py              # Semantic cache
│   ├── build_db.py           # SQLite builder (complete)
│   ├── config.py             # Environment config (complete)
│   └── tracing.py            # Request tracing (complete)
├── solution/                 # Reference implementation
├── tests/
│   ├── conftest.py           # Test fixtures
│   └── test_app.py           # API tests
└── README.md
```

## Setup

```bash
# From module-12-productionisation/exercises/05-movie-night

# 1. Install dependencies
#    Option A - pip (venv active):
pip install fastapi uvicorn openai chromadb python-dotenv numpy
#    Option B - uv (from the repo root): uv sync --extra rag

# 2. Set your API key
export OPENAI_API_KEY=sk-...

# 3. Run the server (solution) — use starter.app:app for your version
#    Option A (venv active):
uvicorn solution.app:app --reload --port 8001
#    Option B (uv):
uv run --extra rag uvicorn solution.app:app --reload --port 8001
```

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| POST | `/api/recommend` | Mood-based movie recommendations (RAG) |
| POST | `/api/query` | Natural language → SQL data queries |
| GET | `/api/movie/{id}` | Full movie details |
| GET | `/api/schema` | Database schema |

### Example Requests

```bash
# Get mood-based recommendations
curl -X POST http://localhost:8001/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "something mind-bending and thought-provoking"}'

# Ask a data question
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top 5 highest rated movies?"}'
```

## Step-by-Step Guide

Work through the `starter/` files in this order:

### Step 1: Guardrails (`guardrails.py`)

Start here — it has no dependencies on other files.

- `validate_sql()` — check for dangerous SQL keywords and multi-statement queries
- `sanitize_output()` — truncate large result sets and long string values

### Step 2: SQL Pipeline (`sql.py`)

Depends on `guardrails.py`.

- `get_schema()` — read SQLite schema using `sqlite_master`
- `text_to_sql()` — prompt the LLM to generate a SELECT query from natural language
- `safe_execute()` — validate then execute, return rows as dicts
- `format_chart_data()` — detect numeric/label columns, suggest chart type

### Step 3: RAG Pipeline (`rag.py`)

Independent of SQL — can work on this in parallel.

- `build_index()` — embed movie plots into ChromaDB in batches
- `search_by_mood()` — vector search with cosine similarity
- `rerank()` — ask the LLM to reorder results by relevance

### Step 4: Cache (`cache.py`)

Depends on understanding the embedding flow.

- `get()` — embed query, find closest cached entry above threshold
- `set()` — store embedding + result, evict expired entries

### Step 5: App (`app.py`)

Wire everything together.

- `lifespan()` — load data, build DB, create vector index
- `recommend()` — cache check → search → rerank → cache store
- `query()` — cache check → schema → text-to-SQL → execute → chart → cache store
- `get_movie()` / `get_schema()` — simple lookups

## Running Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-12-productionisation/exercises/05-movie-night
python -m pytest tests/ -v

# Option B - uv (no activation needed):
cd module-12-productionisation/exercises/05-movie-night
uv run --extra dev pytest tests/ -v
```
