# Exercise 4: AI Personal Assistant (Compass)

Build **Compass**, a personalised AI assistant that manages your calendar, searches your notes, tracks reminders, and checks the weather — all through natural conversation with tool calling and SSE streaming.

## Techniques → Module Reference

| Technique | Module | File |
|---|---|---|
| Tool calling & agent loop | Module 2 — Tool Calling | `agent.py` |
| RAG over personal notes | Module 5 — RAG Fundamentals | `rag.py` |
| Vector embeddings (ChromaDB) | Module 5 — RAG Fundamentals | `rag.py` |
| Structured output (JSON) | Module 4 — Structured Output | `tools.py` |
| SSE streaming | Module 1 — Working with the LLM | `app.py` |
| Semantic caching | Module 12 — Productionisation | `cache.py` |
| PII redaction / guardrails | Module 12 — Productionisation | `guardrails.py` |
| Request tracing | Module 12 — Productionisation | `tracing.py` |
| Token budget tracking | Module 12 — Productionisation | `guardrails.py` |

## Setup

```bash
# From the exercise directory
cd module-12-productionisation/exercises/04-personal-assistant

# Set your OpenAI API key
export OPENAI_API_KEY=your-key-here

# Install dependencies (from project root)
pip install openai fastapi uvicorn chromadb python-dotenv sse-starlette numpy
```

## Running the Solution

```bash
# Start the API server
uvicorn solution.app:app --reload --port 8004

# Health check
curl http://localhost:8004/api/health

# Chat (SSE stream)
curl -N -X POST http://localhost:8004/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What do I have on my calendar this week?", "history": []}'

# List calendar
curl http://localhost:8004/api/calendar

# Search notes
curl "http://localhost:8004/api/notes/search?q=recipe"
```

## Step-by-Step Guide

Work through the starter files in this order:

### Step 1: RAG Pipeline (`rag.py`)
Build the notes vector index. This is the same pattern from Module 5:
- Create a ChromaDB in-memory collection
- Embed each note's title + content using OpenAI embeddings
- Implement `search_notes` to query by vector similarity

### Step 2: Tool Implementations (`tools.py`)
Implement each tool function. These read/write the JSON data files:
- `search_notes` — wraps the RAG search
- `get_calendar` / `add_calendar_event` / `delete_calendar_event` — CRUD on calendar.json
- `get_reminders` / `add_reminder` — read/write reminders.json
- `get_weather` — return mock data

### Step 3: Agent Loop (`agent.py`)
This is the heart of the assistant:
- Define `TOOL_DEFINITIONS` — OpenAI function schemas for each tool
- Build `_build_system_prompt()` using preferences.json
- Implement `run_assistant()` — the synchronous tool-calling loop
- Implement `run_assistant_stream()` — the streaming variant

### Step 4: Guardrails (`guardrails.py`)
Add safety features:
- `confirm_destructive_action` — returns a confirmation prompt
- `redact_pii` — regex-based email/phone/NI number redaction
- `TokenBudget` — tracks and enforces token limits

### Step 5: Semantic Cache (`cache.py`)
Avoid redundant API calls:
- `_embed` — embed a query with OpenAI
- `_cosine_similarity` — numpy dot product
- `get` / `set` — cache lookup and storage with TTL

### Step 6: FastAPI App (`app.py`)
Wire everything together:
- Build the notes index on startup (lifespan)
- Implement `/api/chat` with SSE streaming, cache, and PII redaction
- Implement CRUD endpoints for calendar and reminders
- Add notes search endpoint

## Running Tests

```bash
cd module-12-productionisation/exercises/04-personal-assistant
python -m pytest tests/ -v
```

## Architecture

```
User message
    │
    ▼
┌──────────┐    cache hit?    ┌──────────────┐
│ /api/chat │───────────────▶│ SemanticCache │
└──────────┘   no             └──────────────┘
    │
    ▼
┌──────────────┐  tool calls  ┌───────────┐
│  Agent Loop  │────────────▶│   Tools   │
│ (OpenAI API) │◀────────────│           │
└──────────────┘  results     └───────────┘
    │                              │
    │                    ┌─────────┼─────────┐
    │                    ▼         ▼         ▼
    │               calendar  reminders   notes
    │               .json     .json      (ChromaDB)
    ▼
┌──────────────┐
│ PII Redaction│
└──────────────┘
    │
    ▼
  SSE Stream → Client
```
