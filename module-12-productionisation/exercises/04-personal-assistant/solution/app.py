"""FastAPI personal assistant backend with SSE streaming."""

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
    global notes_collection
    print("Loading data and building notes index...")
    notes = _load_json("notes.json")
    notes_collection = build_notes_index(notes)
    print(f"Indexed {len(notes)} notes.")
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
    """Main chat endpoint with SSE streaming."""
    message = body.get("message", "")
    history = body.get("history", [])

    trace = TraceContext()

    cached = None
    if not history:
        cache_span = trace.start_span("cache_lookup")
        try:
            cached = semantic_cache.get(message)
        except Exception:
            cached = None
        trace.end_span(cache_span, metadata={"hit": cached is not None})

    if cached:
        async def cached_stream():
            yield {"event": "message", "data": json.dumps({"content": cached, "cached": True})}
            yield {"event": "done", "data": json.dumps({"trace": trace.summary()})}
        return EventSourceResponse(cached_stream())

    async def event_stream():
        agent_span = trace.start_span("agent")
        full_response = ""
        try:
            async for chunk in run_assistant_stream(message, history, notes_collection):
                full_response += chunk
                yield {"event": "message", "data": json.dumps({"content": chunk})}

            full_response = redact_pii(full_response)
            trace.end_span(agent_span, metadata={"response_length": len(full_response)})

            if not history:
                try:
                    semantic_cache.set(message, full_response)
                except Exception:
                    pass
        except Exception as e:
            trace.end_span(agent_span, status="error", metadata={"error": str(e)})
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

        yield {"event": "done", "data": json.dumps({"trace": trace.summary()})}

    return EventSourceResponse(event_stream())


@app.get("/api/calendar")
async def list_calendar():
    """List upcoming calendar events."""
    events = _load_json("calendar.json")
    return {"events": events}


@app.post("/api/calendar")
async def create_calendar_event(body: dict):
    """Add a new calendar event."""
    from .tools import add_calendar_event
    result = add_calendar_event(
        title=body["title"],
        date=body["date"],
        time=body["time"],
        duration=body.get("duration", 60),
        location=body.get("location", ""),
        notes=body.get("notes", ""),
    )
    return {"result": result}


@app.delete("/api/calendar/{event_id}")
async def remove_calendar_event(event_id: str):
    """Delete a calendar event."""
    from .tools import delete_calendar_event
    result = delete_calendar_event(event_id)
    return {"result": result}


@app.get("/api/reminders")
async def list_reminders():
    """List active reminders."""
    reminders = _load_json("reminders.json")
    active = [r for r in reminders if not r.get("completed")]
    return {"reminders": active}


@app.get("/api/notes/search")
async def search_notes_endpoint(q: str = Query(..., description="Search query")):
    """RAG search over notes."""
    from .rag import search_notes
    trace = TraceContext()
    search_span = trace.start_span("notes_search")
    results = search_notes(q, notes_collection, k=5)
    trace.end_span(search_span, metadata={"results": len(results)})
    return {"results": results, "trace": trace.summary()}
