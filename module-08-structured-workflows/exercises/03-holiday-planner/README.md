# Exercise 03 — Holiday Planner

## Recap

This exercise pulls together everything from the module — ReAct agents, Plan-and-Execute orchestration, and MCP tool servers — into a complete holiday planning application.

The architecture has three layers:

```
┌──────────────────────────────────────────┐
│           FastAPI Backend                │
│  POST /chat  ─  POST /plan  ─  GET /health│
│                                          │
│  ┌──────────────────────────────────┐    │
│  │  Plan-and-Execute Orchestrator   │    │
│  │  (planner.py)                    │    │
│  │                                  │    │
│  │  ┌──────────────────────────┐    │    │
│  │  │   ReAct Agent            │    │    │
│  │  │   (react_agent.py)       │    │    │
│  │  └──────────────────────────┘    │    │
│  └──────────────────────────────────┘    │
│                    │                      │
│                    ▼                      │
│  ┌──────────────────────────────────┐    │
│  │   MCP Tool Server               │    │
│  │   (server.py)                    │    │
│  │   - search_web                   │    │
│  │   - remember_preference          │    │
│  │   - recall_preferences           │    │
│  │   - search_flights               │    │
│  │   - search_hotels                │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

The **MCP server** provides domain-specific tools (flight/hotel search, preference storage). The **ReAct agent** uses those tools to execute individual steps. The **Plan-and-Execute orchestrator** manages the overall research plan. The **FastAPI backend** ties it all together with streaming SSE responses.

## What you build

Two files to complete:

1. **`server.py`** — a FastMCP server with holiday planning tools
2. **`start.py`** — a FastAPI backend that uses plan-and-execute

The ReAct agent (`react_agent.py`) and planner (`planner.py`) are provided from previous exercises.

## Step-by-step

### 1. Implement the MCP server tools (`server.py`)

Five tools for the holiday planning domain:

| Tool | Description |
|---|---|
| `search_web(query)` | Web search using httpx + DuckDuckGo Lite |
| `remember_preference(key, value)` | Store a user preference (e.g. "budget": "moderate") |
| `recall_preferences()` | Return all stored preferences |
| `search_flights(origin, destination, date)` | Search for flights (mock results) |
| `search_hotels(location, checkin, checkout)` | Search for hotels (mock results) |

**Flight/hotel mock data** should return realistic-looking results with airline names, prices, durations, star ratings, etc.

### 2. Implement the FastAPI backend (`start.py`)

Three endpoints:

| Endpoint | Description |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` |
| `POST /plan` | Takes `{"message": str}`, generates a plan, returns `{"plan": [...]}` |
| `POST /chat` | Takes `{"message": str}`, runs plan-and-execute, streams SSE events |

The `/chat` endpoint should stream Server-Sent Events so the frontend can show progress:

```
data: {"type": "plan", "steps": [...]}

data: {"type": "step_start", "step": 1, "description": "..."}

data: {"type": "step_done", "step": 1, "result": "..."}

data: {"type": "answer", "content": "..."}
```

### 3. Wire up MCP tools

The FastAPI backend needs to make the MCP tools available to the ReAct agent. The simplest approach: import the tool functions directly from `server.py` and register them as ReAct tools.

### 4. Test it

Run the MCP server standalone to verify tools work:

```bash
python server.py
```

Run the FastAPI backend:

```bash
pip install "fastapi[standard]" uvicorn
uvicorn start:app --reload --port 8000
```

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

Test the plan endpoint:

```bash
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a week-long trip to Tokyo in April"}'
```

Test the chat endpoint (SSE):

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a week-long trip to Tokyo in April"}'
```

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- FastAPI app has a working `/health` endpoint
- `/plan` returns JSON with a plan
- MCP server defines the expected tools

## Stretch goals

- Add a `search_activities(location, interests)` tool for attraction recommendations
- Implement real flight search using a public API (e.g. Amadeus sandbox)
- Add a `/preferences` endpoint that returns stored user preferences
- Build a budget calculator tool that sums up flight + hotel costs
