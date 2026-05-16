"""FastAPI personal assistant backend with SSE streaming.

Endpoints:
- GET  /api/health           — health check
- POST /api/chat             — main chat with SSE streaming
- GET  /api/calendar         — list upcoming events
- POST /api/calendar         — add a new event
- DELETE /api/calendar/{id}  — delete an event
- GET  /api/reminders        — list active reminders
- GET  /api/notes/search     — RAG search over notes (?q=query)
"""

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .agent import run_assistant, run_assistant_stream
from .cache import SemanticCache
from .config import DATA_DIR
from .guardrails import TokenBudget, redact_pii
from .rag import build_notes_index
from .tracing import TraceContext

notes_collection = None
semantic_cache = SemanticCache()
token_budget = TokenBudget()


def _load_json(filename: str) -> list | dict:
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load data files and build the notes vector index."""
    global notes_collection
    # TODO: Load notes.json and build the ChromaDB index
    # notes = _load_json("notes.json")
    # notes_collection = build_notes_index(notes)
    print("Startup complete (index not yet built — implement lifespan)")
    yield


app = FastAPI(title="Compass — Personal Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "assistant": "Compass"}


@app.post("/api/chat")
async def chat(body: dict):
    """Main chat endpoint with SSE streaming.

    Request body: {"message": str, "history": list}

    Steps:
    1. Check the semantic cache for a cached response
    2. If cache miss, run the agent with streaming
    3. Apply PII redaction to the response
    4. Cache the result for future similar queries
    5. Return as Server-Sent Events
    """
    message = body.get("message", "")
    history = body.get("history", [])

    trace = TraceContext()

    # TODO: Check semantic cache for first messages (no history)

    async def event_stream():
        # TODO: Run the agent with streaming
        # Yield SSE events: {"event": "message", "data": json.dumps({"content": chunk})}
        # On completion: {"event": "done", "data": json.dumps({"trace": trace.summary()})}
        yield {"event": "message", "data": json.dumps({"content": "Chat not yet implemented."})}
        yield {"event": "done", "data": json.dumps({"trace": trace.summary()})}

    return EventSourceResponse(event_stream())


@app.get("/api/calendar")
async def list_calendar():
    """List upcoming calendar events."""
    # TODO: Load and return calendar.json
    return {"events": []}


@app.post("/api/calendar")
async def create_calendar_event(body: dict):
    """Add a new calendar event."""
    # TODO: Call tools.add_calendar_event with body params
    return {"result": "Not yet implemented"}


@app.delete("/api/calendar/{event_id}")
async def remove_calendar_event(event_id: str):
    """Delete a calendar event."""
    # TODO: Call tools.delete_calendar_event
    return {"result": "Not yet implemented"}


@app.get("/api/reminders")
async def list_reminders():
    """List active reminders."""
    # TODO: Load reminders.json and filter for active (not completed)
    return {"reminders": []}


@app.get("/api/notes/search")
async def search_notes_endpoint(q: str = Query(..., description="Search query")):
    """RAG search over notes."""
    # TODO: Use rag.search_notes to search the collection
    return {"results": [], "trace": ""}
