"""
Exercise 03 — Live Tools Agent (solution)
Console agent connecting to the live tools MCP server solution.

Run:  python solution.py
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
    "You are the DSS Pathfinder ship AI. You can fetch web pages, save notes, "
    "and read them back. Use your tools to help the user research and organise "
    "information. Be concise."
)


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


async def run_agent(
    session: ClientSession,
    client: openai.OpenAI,
    openai_tools: list[dict],
    max_steps: int = 10,
) -> None:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("DSS Pathfinder Live Agent ready. Type a question (or 'quit').\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        for _ in range(max_steps):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=openai_tools,
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    result = await session.call_tool(name, arguments=args)
                    text = result.content[0].text if result.content else ""
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": text,
                    })
            elif msg.content:
                messages.append(msg)
                print(f"\nAgent: {msg.content}\n")
                break
            else:
                print("\nAgent: (no response)\n")
                break


async def main() -> None:
    server_script = str(Path(__file__).parent / "solution_server.py")

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
