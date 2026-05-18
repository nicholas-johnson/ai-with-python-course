"""
Exercise 3: Multimodal -- Vision and Audio -- SOLUTION
"""

import asyncio
import io
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
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
            command=sys.executable,
            args=[str(Path(__file__).parent / "solution_server.py")],
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


class VisionResponse(BaseModel):
    description: str
    key_points: list[str]


async def execute_tool_calls(session: MCPConnection, tool_calls) -> list[dict]:
    """Execute MCP tool calls and return tool-result messages."""
    results = []
    for tc in tool_calls:
        name = tc.function.name
        args = json.loads(tc.function.arguments)
        content = await session.call_tool(name, args)
        results.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": content,
        })
    return results


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Send audio bytes to OpenAI Whisper and return the transcript text."""
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return transcript.text


async def analyze_image(image_b64: str, prompt: str) -> dict:
    """Send a base64 image to GPT-4o and return {description, key_points}."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an image analysis assistant. Respond with a JSON object "
                    'containing "description" (string) and "key_points" (list of strings). '
                    "Only output valid JSON, no markdown."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


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
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}),
                    }
                    await asyncio.sleep(0)

                tool_results = await execute_tool_calls(mcp_conn, assistant_msg.tool_calls)

                for tc, result_msg in zip(assistant_msg.tool_calls, tool_results):
                    yield {
                        "event": "tool_result",
                        "data": json.dumps({"name": tc.function.name, "content": result_msg["content"]}),
                    }
                    await asyncio.sleep(0)

                messages.extend(tool_results)
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


@app.post("/vision")
async def vision(req: VisionRequest):
    result = await analyze_image(req.image, req.prompt)
    return VisionResponse(
        description=result.get("description", ""),
        key_points=result.get("key_points", []),
    )


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = await transcribe_audio(audio_bytes)
    return {"transcript": text}
