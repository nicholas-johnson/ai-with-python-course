"""
Exercise 1: Streaming Chat API -- SOLUTION
"""

import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

client = OpenAI()

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful research assistant. You provide clear, accurate, "
        "and well-structured answers. When you don't know something, say so."
    ),
}


class ChatRequest(BaseModel):
    messages: list[dict]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        messages = [SYSTEM_MESSAGE] + req.messages
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
        )

        full_content = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_content += delta.content
                yield {
                    "event": "token",
                    "data": json.dumps({"token": delta.content}),
                }

        yield {
            "event": "done",
            "data": json.dumps({"role": "assistant", "content": full_content}),
        }

    return EventSourceResponse(generate())
