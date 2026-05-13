"""
Exercise 02 — Streaming API
FastAPI chat endpoint with SSE streaming.
"""

import asyncio
import json
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


async def fake_stream(text: str):
    """Simulate token-by-token streaming. Yields one word at a time."""
    words = text.split()
    for i, word in enumerate(words):
        prefix = " " if i > 0 else ""
        yield prefix + word
        await asyncio.sleep(0.01)


def create_app() -> FastAPI:
    app = FastAPI(title="DSS Pathfinder — Chat Streaming API")

    # TODO: implement POST /chat endpoint
    # - Get or create session_id
    # - Append user message to session
    # - Generate response text (use fake_stream with a simple reply)
    # - Return EventSourceResponse that yields:
    #   1. {"event": "session", "data": json.dumps({"session_id": ...})}
    #   2. {"event": "token", "data": json.dumps({"token": ...})} for each token
    #   3. {"event": "done", "data": json.dumps({"full_response": ...})}
    # - After streaming, append assistant message to session

    # TODO: implement GET /sessions/{session_id}
    # - Return {"session_id": ..., "messages": [...]} or 404

    return app


app = create_app()
