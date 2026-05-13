"""
Exercise 2: Tool-Calling Chat API
===================================
Extend the Exercise 1 chat API with MCP tool support.

Ships with the Exercise 1 solution. You need to:
  1. Build server.py (the MCP server with research tools)
  2. Connect to the MCP server on startup
  3. Extend /chat with a tool-calling loop
  4. Add GET /tools endpoint

Run with:  uvicorn start:app --reload --port 8000
"""

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# TODO: import asyncio, mcp client modules

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

client = OpenAI()

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful research assistant with access to tools. "
        "Use fetch_url to retrieve web pages. Use the note tools to "
        "save, list, read, and search research notes. Be thorough and accurate."
    ),
}


class ChatRequest(BaseModel):
    messages: list[dict]


@app.get("/health")
async def health():
    return {"status": "ok"}


# TODO: Add a lifespan context manager that:
#   1. Connects to the MCP server (server.py) via stdio_client
#   2. Discovers tools and stores them on app.state
#   3. Yields
#   4. Cleans up on shutdown


# TODO: Write a helper function mcp_to_openai_tools(mcp_tools)
#   that converts MCP tool definitions to OpenAI function-calling format


# TODO: Add GET /tools endpoint that returns the tool list


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        messages = [SYSTEM_MESSAGE] + req.messages

        # TODO: Get tools from app.state (if available)
        tools = []

        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            tools=tools if tools else None,
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

        # TODO: Add tool-calling loop here
        #   If the response contains tool_calls:
        #     1. Yield "tool_call" SSE events
        #     2. Execute tools via MCP session
        #     3. Yield "tool_result" SSE events
        #     4. Feed results back and call the LLM again
        #     5. Repeat until the LLM returns text content

        yield {
            "event": "done",
            "data": json.dumps({"role": "assistant", "content": full_content}),
        }

    return EventSourceResponse(generate())
