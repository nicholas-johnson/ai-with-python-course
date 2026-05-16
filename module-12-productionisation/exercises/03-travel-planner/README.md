# Exercise 3 — AI Travel Planner

An agentic travel planning API that uses RAG search, tool calling, and guardrails to generate day-by-day itineraries.

## Techniques & Modules

| Technique | Module Reference |
|-----------|-----------------|
| Tool calling & agentic loops | Module 2 — Tool Calling |
| RAG with ChromaDB embeddings | Module 5 — RAG Fundamentals |
| Structured output (JSON itinerary) | Module 4 — Structured Output |
| Guardrails & safety checks | Module 12 — Productionisation |
| Tracing & observability | Module 12 — Productionisation |
| FastAPI backend | Module 12 — Productionisation |

## Architecture

```
POST /api/plan → agent.py (agentic loop)
                    ├── tools: search_attractions (RAG)
                    ├── tools: get_weather (mock)
                    ├── tools: estimate_budget
                    └── tools: estimate_travel_time
                 → guardrails.py (budget + safety validation)
                 → tracing.py (request tracing)

POST /api/search → rag.py (vector search over destinations)
GET /api/destination/{id} → direct lookup
GET /api/weather?city=X → mock weather
```

## Running the Solution

```bash
# From the exercise directory
cd module-12-productionisation/exercises/03-travel-planner

# Install dependencies
pip install openai fastapi uvicorn chromadb python-dotenv

# Set your API key
export OPENAI_API_KEY=your-key-here

# Run the server
uvicorn solution.app:app --reload --port 8002
```

## Running Tests

```bash
pytest tests/ -v
```

## Step-by-Step Guide (Starter)

### Step 1: Implement `tools.py`

Start with the simplest file. Each function returns mock data using deterministic random seeds:

- `get_weather`: seed from city name → pick weather pattern → add variance
- `estimate_budget`: look up rates by level → calculate totals
- `estimate_travel_time`: seed from location names → random 10-90 min

### Step 2: Implement `guardrails.py`

Two safety functions:

- `validate_budget`: loop through itinerary days, flag any exceeding the limit
- `check_safety`: scan destination text for advisory keywords

### Step 3: Implement `rag.py`

Build the search index:

1. Create ChromaDB in-memory client and collection
2. Loop destinations → create document strings with name + description + tags
3. Loop attractions within each destination → create attraction documents
4. Batch embed all documents using OpenAI embeddings API
5. Add to collection with metadata for filtering

Implement search functions using `collection.query()` with `where` filters.

### Step 4: Implement `agent.py`

The core agentic loop:

1. Build a system prompt with trip requirements and expected JSON output format
2. Loop up to 8 iterations:
   - Call the LLM with tools available
   - If it returns tool calls → execute them → feed results back
   - If no tool calls → it's done planning
3. Parse the final JSON response
4. Attach trace data

### Step 5: Implement `app.py`

Wire everything together:

- `startup`: load JSON, build index
- `/api/plan`: safety check → agent planning → budget validation
- `/api/search`: vector search → return results
- `/api/destination/{id}`: direct lookup
- `/api/weather`: delegate to tools

### Step 6: Test

Run `pytest tests/ -v` to verify your implementation matches the expected behaviour.
