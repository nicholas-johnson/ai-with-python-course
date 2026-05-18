"""
Exercise 01 — MCP Agent
Console agent that connects to an MCP server, discovers tools, and chats.

Run:  python start.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

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
# 2. Single turn — one LLM call + tool execution loop
# ---------------------------------------------------------------------------

async def run_turn(
    client: openai.OpenAI,
    messages: list[dict],
    session: ClientSession,
    openai_tools: list[dict],
    max_steps: int = 10,
) -> str | None:
    """Handle one LLM turn with tool execution until a final reply.

    Returns the assistant's text reply, or None if max steps exceeded.

    For up to max_steps:
        1. Call client.chat.completions.create(...) with messages and openai_tools
        2. If message.tool_calls: execute each via session.call_tool(), append results
        3. Else if message.content: append and return it
        4. Else: return None
    """
    # TODO: implement
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# 3. Agent REPL — read input, dispatch to run_turn
# ---------------------------------------------------------------------------

async def run_agent(
    session: ClientSession,
    client: openai.OpenAI,
    openai_tools: list[dict],
    max_steps: int = 10,
) -> None:
    """Interactive REPL that dispatches each user message to run_turn."""
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("DSS Pathfinder MCP Agent ready. Type a question (or 'quit').\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})
        reply = await run_turn(client, messages, session, openai_tools, max_steps)

        if reply:
            print(f"\nAgent: {reply}\n")
        else:
            print("\nAgent: (no response)\n")


# ---------------------------------------------------------------------------
# 4. Main — connect to server and run agent
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
