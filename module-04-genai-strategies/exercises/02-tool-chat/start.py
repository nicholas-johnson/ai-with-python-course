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

import asyncio
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

client = OpenAI()

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful research assistant with access to tools. "
        "Use fetch_url to retrieve web pages. Use the note tools to "
        "save, list, read, and search research notes. Be thorough and accurate."
    ),
}


# TODO: Write a helper function mcp_to_openai_tools(mcp_tools)
#   that converts MCP tool definitions to OpenAI function-calling format


# TODO: Implement the MCPConnection class
#   - connect(): launch MCP server via StdioServerParameters, initialize session
#   - disconnect(): clean up session and client context managers
#   - call_tool(name, arguments): call a tool and return the text result


# TODO: Create the mcp_conn instance and a lifespan context manager
#   that connects on startup and disconnects on shutdown


app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class ChatRequest(BaseModel):
    messages: list[dict]


async def execute_tool_calls(session, tool_calls) -> list[dict]:
    """Execute MCP tool calls and return tool-result messages.

    For each tool call:
      1. Extract name and arguments
      2. Call session.call_tool(name, args)
      3. Build a {"role": "tool", "tool_call_id": ..., "content": ...} dict

    Return the list of tool-result message dicts.
    """
    # TODO: implement
    raise NotImplementedError


@app.get("/health")
async def health():
    return {"status": "ok"}


# TODO: Add GET /tools endpoint that returns the tool list


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        messages = [SYSTEM_MESSAGE] + req.messages

        # TODO: Get tools from mcp_conn (if available)
        tools = None

        # TODO: Implement the tool-calling loop:
        #   1. Call the LLM with tools
        #   2. If finish_reason == "tool_calls":
        #      - Yield "tool_call" SSE events
        #      - Use execute_tool_calls() to run them via MCP
        #      - Yield "tool_result" SSE events
        #      - Append results to messages and loop
        #   3. Otherwise, stream the final text response

        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            tools=tools,
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
