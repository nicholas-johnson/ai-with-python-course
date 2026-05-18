"""
Exercise 01 — MCP Agent (provided)
Connects to server.py via stdio, discovers tools, runs an interactive chat loop.
"""

import asyncio
import json
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

SYSTEM_PROMPT = (
    "You are the station power grid AI. Use your tools to answer power "
    "management queries. Be concise."
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


async def run_agent(session, client, openai_tools):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Power Grid Agent ready. Type a question (or 'quit').\n")

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
    server_script = str(Path(__file__).parent / "server.py")
    params = StdioServerParameters(command=sys.executable, args=[server_script])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            openai_tools = mcp_to_openai_tools(tools)

            print(f"Connected. Discovered {len(tools)} tools:")
            for t in openai_tools:
                print(f"  - {t['function']['name']}: {t['function']['description']}")
            print()

            client = openai.OpenAI()
            await run_agent(session, client, openai_tools)


if __name__ == "__main__":
    asyncio.run(main())
