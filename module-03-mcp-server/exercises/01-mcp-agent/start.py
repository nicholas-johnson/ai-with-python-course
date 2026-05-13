"""
Exercise 01 — MCP Agent
Console agent that connects to an MCP server, discovers tools, and chats.

Run:  python start.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import openai
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SYSTEM_PROMPT = (
    "You are the DSS Pathfinder ship AI. Use the available tools to answer "
    "crew and ship queries. Be concise."
)


# ---------------------------------------------------------------------------
# 1. Convert MCP tools to OpenAI format
# ---------------------------------------------------------------------------

def mcp_to_openai_tools(mcp_tools: list) -> list[dict]:
    """Convert a list of MCP Tool objects to OpenAI tool-calling format.

    Each MCP tool has .name, .description, and .inputSchema.
    OpenAI expects:
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
    """
    # TODO: implement
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# 2. Agent loop — ask LLM, call tools via MCP, repeat
# ---------------------------------------------------------------------------

async def run_agent(
    session: ClientSession,
    client: openai.OpenAI,
    openai_tools: list[dict],
    max_steps: int = 10,
) -> None:
    """Interactive console agent loop.

    For each user message:
    1. Send messages + tools to OpenAI.
    2. If the response has tool_calls:
       - For each tool call, use `await session.call_tool(name, arguments=args)`
       - The result has .content — a list of content blocks. Extract the text.
       - Append the tool result to messages and loop.
    3. If the response has content (no tool calls), print it and wait for next input.
    """
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("DSS Pathfinder MCP Agent ready. Type a question (or 'quit').\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        # TODO: implement the tool-calling loop
        # For up to max_steps:
        #   1. Call client.chat.completions.create(...) with messages and openai_tools
        #   2. If message.tool_calls: execute each via session.call_tool(), append results
        #   3. Else if message.content: print and break
        raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# 3. Main — connect to server and run agent
# ---------------------------------------------------------------------------

async def main() -> None:
    server_script = str(Path(__file__).parent / "server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            openai_tools = mcp_to_openai_tools(tools_result.tools)

            print(f"Connected to MCP server. Discovered {len(openai_tools)} tools:")
            for t in openai_tools:
                print(f"  - {t['function']['name']}: {t['function']['description']}")
            print()

            client = openai.OpenAI()
            await run_agent(session, client, openai_tools)


if __name__ == "__main__":
    asyncio.run(main())
