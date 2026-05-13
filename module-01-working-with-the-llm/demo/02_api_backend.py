"""
Demo: FastAPI chat backend with SSE streaming.
Run:  python module-01-working-with-the-llm/demo/02_api_backend.py

Starts a server on port 8002. POST to /chat with {"message": "...", "session_id": "..."}
"""

import asyncio
import json
import uuid

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="DSS Pathfinder — Chat API")

sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


async def fake_stream(text: str):
    """Simulate token-by-token streaming."""
    words = text.split()
    for i, word in enumerate(words):
        prefix = " " if i > 0 else ""
        yield prefix + word
        await asyncio.sleep(0.05)


@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = [
            {"role": "system", "content": "You are the DSS Pathfinder ship AI."},
        ]

    sessions[session_id].append({"role": "user", "content": request.message})

    response_text = f"Acknowledged, Engineer. Processing your request regarding: {request.message}"

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
        return {"error": "Session not found"}
    return {"session_id": session_id, "messages": sessions[session_id]}


if __name__ == "__main__":
    print("Starting chat API on http://127.0.0.1:8002")
    print("POST /chat  — send a message")
    print("GET  /sessions/{id} — view history\n")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")
