"""
Exercise 02 — Multi-server MCP Agent (provided)
Connects to local_server.py (stdio) and server.py (HTTP), wires both to one LLM.
"""

import asyncio
import json
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

SYSTEM_PROMPT = (
    "You are the station AI. You have access to power grid tools AND science lab tools. "
    "Use them to answer queries. Be concise."
)

LOCAL_SERVER = str(Path(__file__).parent / "local_server.py")
HTTP_SERVER_URL = "http://localhost:8000/mcp"


def mcp_to_openai_tools(mcp_tools: list) -> list[dict]:
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


async def run_agent(tool_router, openai_tools):
    client = openai.OpenAI()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Station AI ready (power grid + science lab). Type a question (or 'quit').\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        for _ in range(10):
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=openai_tools
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    session = tool_router[name]
                    print(f"  [tool] {name}({json.dumps(args)})")
                    result = await session.call_tool(name, arguments=args)
                    text = result.content[0].text if result.content else ""
                    print(f"  [result] {text[:120]}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": text,
                    })
            elif msg.content:
                messages.append({"role": "assistant", "content": msg.content})
                print(f"AI> {msg.content}\n")
                break
            else:
                print("AI> (no response)\n")
                break


async def main():
    params = StdioServerParameters(command=sys.executable, args=[LOCAL_SERVER])

    async with stdio_client(params) as (stdio_read, stdio_write):
        async with ClientSession(stdio_read, stdio_write) as power_session:
            await power_session.initialize()

            async with streamablehttp_client(HTTP_SERVER_URL) as (http_read, http_write, _):
                async with ClientSession(http_read, http_write) as lab_session:
                    await lab_session.initialize()

                    tool_router = {}
                    openai_tools = []

                    for tool in (await power_session.list_tools()).tools:
                        tool_router[tool.name] = power_session
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.inputSchema,
                            },
                        })

                    for tool in (await lab_session.list_tools()).tools:
                        tool_router[tool.name] = lab_session
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": tool.inputSchema,
                            },
                        })

                    print(f"Connected to 2 servers. {len(openai_tools)} tools available:")
                    for t in openai_tools:
                        print(f"  - {t['function']['name']}: {t['function']['description']}")
                    print()

                    await run_agent(tool_router, openai_tools)


if __name__ == "__main__":
    asyncio.run(main())
