"""
Exercise 1: Research Chat — Streaming Chat with MCP Tools
==========================================================
Build a FastAPI backend that streams chat from GPT-4o-mini and
executes tools via a provided MCP server.

The MCP server (server.py) is provided — it exposes fetch_url
and note-taking tools. Your job is to wire up the chat loop.

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


# ---------------------------------------------------------------------------
# Provided: MCP connection management (no changes needed)
# ---------------------------------------------------------------------------


class MCPConnection:
    def __init__(self):
        self.session = None
        self.tools = []
        self.openai_tools = []
        self._read = None
        self._write = None
        self._cm = None
        self._session_cm = None

    async def connect(self):
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).parent / "server.py")],
        )
        self._cm = stdio_client(server_params)
        self._read, self._write = await self._cm.__aenter__()
        self._session_cm = ClientSession(self._read, self._write)
        self.session = await self._session_cm.__aenter__()
        await self.session.initialize()

        result = await self.session.list_tools()
        self.tools = result.tools
        self.openai_tools = mcp_to_openai_tools(self.tools)

    async def disconnect(self):
        if self._session_cm:
            await self._session_cm.__aexit__(None, None, None)
        if self._cm:
            await self._cm.__aexit__(None, None, None)

    async def call_tool(self, name: str, arguments: dict) -> str:
        result = await self.session.call_tool(name, arguments)
        return result.content[0].text if result.content else ""


mcp_conn = MCPConnection()


@asynccontextmanager
async def lifespan(app):
    await mcp_conn.connect()
    yield
    await mcp_conn.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class ChatRequest(BaseModel):
    messages: list[dict]


# ---------------------------------------------------------------------------
# TODO 1: Convert MCP tools to OpenAI format
# ---------------------------------------------------------------------------


def mcp_to_openai_tools(mcp_tools):
    """Convert a list of MCP tool definitions to OpenAI function-calling format.

    Each tool becomes:
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}

    Hint: each MCP tool has .name, .description, and .inputSchema attributes.
    """
    # TODO: implement
    raise NotImplementedError


# ---------------------------------------------------------------------------
# TODO 2: Execute tool calls via MCP
# ---------------------------------------------------------------------------


async def execute_tool_calls(session: MCPConnection, tool_calls) -> list[dict]:
    """Execute MCP tool calls and return tool-result messages.

    For each tool call:
      1. Extract tc.function.name and json.loads(tc.function.arguments)
      2. Call session.call_tool(name, args)
      3. Build a {"role": "tool", "tool_call_id": tc.id, "content": ...} dict

    Return the list of tool-result message dicts.
    """
    # TODO: implement
    raise NotImplementedError


# ---------------------------------------------------------------------------
# TODO 3: Endpoints
# ---------------------------------------------------------------------------


# TODO: GET /health -> {"status": "ok"}


# TODO: GET /tools -> list of {"name": ..., "description": ...} from mcp_conn.tools


# ---------------------------------------------------------------------------
# TODO 4: Streaming chat with tool-calling loop
# ---------------------------------------------------------------------------


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        messages = [SYSTEM_MESSAGE] + req.messages
        tools = mcp_conn.openai_tools if mcp_conn.openai_tools else None

        # TODO: Implement the tool-calling loop:
        #
        # while True:
        #   1. Call client.chat.completions.create(model, messages, tools)
        #      (non-streaming, to check for tool calls)
        #
        #   2. If choice.finish_reason == "tool_calls":
        #      - Append the assistant message (with tool_calls) to messages
        #      - Yield {"event": "tool_call", "data": ...} for each tool call
        #      - Use execute_tool_calls() to run them via MCP
        #      - Yield {"event": "tool_result", "data": ...} for each result
        #      - Append tool results to messages, then continue the loop
        #
        #   3. Otherwise (text response):
        #      - Make a STREAMING call to get the final answer token by token
        #      - Yield {"event": "token", "data": {"token": "..."}} for each chunk
        #      - Yield {"event": "done", "data": {"role": "assistant", "content": ...}}
        #      - Break

        # Placeholder: simple streaming without tools (replace with the loop above)
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
