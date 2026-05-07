"""
Exercise 02 — Streaming API (solution)
"""

import asyncio
import json
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


async def fake_stream(text: str):
    words = text.split()
    for i, word in enumerate(words):
        prefix = " " if i > 0 else ""
        yield prefix + word
        await asyncio.sleep(0.01)


def create_app() -> FastAPI:
    app = FastAPI(title="DSS Pathfinder — Chat Streaming API")

    @app.post("/chat")
    async def chat(request: ChatRequest):
        session_id = request.session_id or str(uuid.uuid4())
        if session_id not in sessions:
            sessions[session_id] = [
                {"role": "system", "content": "You are the DSS Pathfinder ship AI."},
            ]

        sessions[session_id].append({"role": "user", "content": request.message})
        response_text = f"Acknowledged. Processing: {request.message}"

        async def event_generator():
            yield {"event": "session", "data": json.dumps({"session_id": session_id})}

            full_response = []
            async for token in fake_stream(response_text):
                full_response.append(token)
                yield {"event": "token", "data": json.dumps({"token": token})}

            final = "".join(full_response)
            sessions[session_id].append({"role": "assistant", "content": final})
            yield {"event": "done", "data": json.dumps({"full_response": final})}

        return EventSourceResponse(event_generator())

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "messages": sessions[session_id]}

    return app


app = create_app()
