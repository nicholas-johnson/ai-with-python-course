"""
Exercise 01 — MCP Agent (provided)
Connects to server.py via stdio, discovers tools, runs an interactive chat loop.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

SYSTEM_PROMPT = (
    "You are the station power grid AI. Use your tools to answer power "
    "management queries. Be concise."
)


def mcp_to_openai_tools(mcp_tools: list) -> list[dict]:
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
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
            response = client.responses.create(
                model=MODEL, reasoning={"effort": "none"}, input=messages, tools=openai_tools
            )
            calls = [item for item in response.output if item.type == "function_call"]

            if calls:
                messages += response.output
                for tc in calls:
                    name = tc.name
                    args = json.loads(tc.arguments)
                    print(f"  [tool] {name}({json.dumps(args)})")
                    result = await session.call_tool(name, arguments=args)
                    text = result.content[0].text if result.content else ""
                    print(f"  [result] {text[:120]}")
                    messages.append({
                        "type": "function_call_output",
                        "call_id": tc.call_id,
                        "output": text,
                    })
            elif response.output_text:
                messages.append({"role": "assistant", "content": response.output_text})
                print(f"AI> {response.output_text}\n")
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
                print(f"  - {t['name']}: {t['description']}")
            print()

            client = openai.OpenAI()
            await run_agent(session, client, openai_tools)


if __name__ == "__main__":
    asyncio.run(main())
