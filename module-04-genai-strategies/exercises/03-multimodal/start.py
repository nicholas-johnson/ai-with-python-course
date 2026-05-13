"""
Exercise 3: Multimodal -- Vision and Audio
============================================
Extend the Research Assistant with two new endpoints:
  POST /vision     -> analyse an image with GPT-4o
  POST /transcribe -> transcribe audio with Whisper

Ships with the Exercise 2 solution (chat + MCP tools).

Run with:  uvicorn start:app --reload --port 8000
"""

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

client = OpenAI()

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful research assistant with access to tools. "
        "Use fetch_url to retrieve web pages. Use the note tools to "
        "save, list, read, and search research notes. Be thorough and accurate."
    ),
}


def mcp_to_openai_tools(mcp_tools):
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        }
        for tool in mcp_tools
    ]


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
            command="python", args=["solution_server.py"]
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


class VisionRequest(BaseModel):
    image: str
    prompt: str = "Describe and analyse this image in detail."


# -- Provided endpoints (from Exercise 2 solution) --


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tools")
async def list_tools():
    return [
        {"name": t.name, "description": t.description or ""} for t in mcp_conn.tools
    ]


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        messages = [SYSTEM_MESSAGE] + req.messages
        tools = mcp_conn.openai_tools if mcp_conn.openai_tools else None

        while True:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                assistant_msg = choice.message
                messages.append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in assistant_msg.tool_calls
                        ],
                    }
                )

                for tc in assistant_msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)

                    yield {
                        "event": "tool_call",
                        "data": json.dumps({"name": name, "arguments": args}),
                    }
                    await asyncio.sleep(0)

                    result = await mcp_conn.call_tool(name, args)

                    yield {
                        "event": "tool_result",
                        "data": json.dumps({"name": name, "content": result}),
                    }
                    await asyncio.sleep(0)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        }
                    )

                continue

            content = choice.message.content or ""

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

            if not full_content:
                full_content = content

            yield {
                "event": "done",
                "data": json.dumps(
                    {"role": "assistant", "content": full_content}
                ),
            }
            break

    return EventSourceResponse(generate())


# -- TODO: Add these two new endpoints --


# TODO: POST /vision
#   1. Accept VisionRequest (image as base64, prompt)
#   2. Send to GPT-4o with the image as a data URL
#   3. Return {"description": "...", "key_points": [...]}


# TODO: POST /transcribe
#   1. Accept an audio file upload (UploadFile)
#   2. Send to OpenAI Whisper API
#   3. Return {"transcript": "..."}
