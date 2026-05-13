"""
Exercise 1: Streaming Chat API
===============================
Build a FastAPI app with two endpoints:
  GET  /health  -> {"status": "ok"}
  POST /chat    -> SSE stream of token/done events

Run with:  uvicorn start:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# TODO: import EventSourceResponse from sse_starlette.sse
# TODO: import OpenAI from openai
# TODO: import json

app = FastAPI()

# TODO: Add CORS middleware (allow all origins for local dev)


class ChatRequest(BaseModel):
    messages: list[dict]


# TODO: Create GET /health endpoint that returns {"status": "ok"}


# TODO: Create POST /chat endpoint that:
#   1. Creates an OpenAI client
#   2. Calls client.chat.completions.create() with stream=True
#   3. Yields SSE events:
#      - event: "token", data: {"token": "<text>"}  for each chunk
#      - event: "done",  data: {"role": "assistant", "content": "<full text>"}  at the end
#   4. Returns EventSourceResponse(generate())
