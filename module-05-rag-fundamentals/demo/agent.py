"""
Module 5 Demo — agent.py
===========================
Console agent that connects to the RAG MCP server and chats using tool calling.

Spawns server.py as a subprocess via stdio, discovers tools, and runs
an OpenAI tool-calling loop.

Usage:
  python agent.py

Requires:
  - Data ingested via ingest.py
  - OPENAI_API_KEY environment variable
"""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SERVER_SCRIPT = str(Path(__file__).parent / "server.py")
MODEL = "gpt-4o-mini"


def mcp_to_openai_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to OpenAI function-calling format."""
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


async def agent_loop(session, openai_tools, mcp_tools_map):
    """Interactive agent loop with tool calling."""
    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a research assistant with access to a document search system "
                "containing ship logs. Use the available tools to find and retrieve "
                "information. Always cite your sources."
            ),
        }
    ]

    print("Type a question, /tools to list tools, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/tools":
            for name, tool in mcp_tools_map.items():
                desc = tool.description or "No description"
                print(f"  - {name}: {desc}")
            continue

        messages.append({"role": "user", "content": user_input})

        while True:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=openai_tools,
            )
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                for tc in choice.message.tool_calls:
                    fn_name = tc.function.name
                    fn_args = json.loads(tc.function.arguments)
                    print(f"  [tool_call] {fn_name}({json.dumps(fn_args)})")

                    result = await session.call_tool(fn_name, fn_args)
                    result_text = result.content[0].text if result.content else "No result"
                    preview = result_text[:200].replace("\n", " ")
                    print(f"  [tool_result] {preview}...")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result_text,
                        }
                    )
            else:
                answer = choice.message.content
                messages.append({"role": "assistant", "content": answer})
                print(f"Agent: {answer}\n")
                break


async def async_main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
    )

    print("=" * 50)
    print("  Module 5 Demo — RAG Agent")
    print("=" * 50)
    print("\nConnecting to RAG MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools
            openai_tools = mcp_to_openai_tools(mcp_tools)
            mcp_tools_map = {t.name: t for t in mcp_tools}

            print(f"Connected. {len(mcp_tools)} tools available.\n")
            await agent_loop(session, openai_tools, mcp_tools_map)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
