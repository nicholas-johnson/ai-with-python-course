"""
Exercise 3 -- Solution
========================
Console agent connected to the RAG MCP server via stdio.

Run:  python solution.py
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

SERVER_SCRIPT = "solution_server.py"


def mcp_to_openai_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        }
        for tool in mcp_tools
    ]


async def run_turn(client, messages, session, openai_tools, max_steps: int = 10) -> str:
    """Execute one conversational turn: call the LLM, handle tool calls, return final text."""
    for _ in range(max_steps):
        response = client.responses.create(
            model=MODEL, reasoning={"effort": "none"}, input=messages, tools=openai_tools,
        )
        calls = [item for item in response.output if item.type == "function_call"]

        if not calls:
            answer = response.output_text
            messages.append({"role": "assistant", "content": answer})
            return answer

        messages += response.output
        for tc in calls:
            fn_name = tc.name
            fn_args = json.loads(tc.arguments)
            print(f"  [tool_call] {fn_name}({json.dumps(fn_args)})")

            result = await session.call_tool(fn_name, fn_args)
            result_text = result.content[0].text if result.content else "No result"
            print(f"  [tool_result] {result_text[:150].replace(chr(10), ' ')}...")

            messages.append({"type": "function_call_output", "call_id": tc.call_id, "output": result_text})

    return "(max tool steps reached)"


async def agent_loop(session, openai_tools, mcp_tools_map):
    """Interactive REPL: read user input, dispatch to run_turn."""
    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a research assistant with access to a document search system. "
                "Use the available tools to find and retrieve information from scout logs. "
                "Always cite your sources."
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
                print(f"  - {name}: {tool.description or 'No description'}")
            continue

        messages.append({"role": "user", "content": user_input})
        answer = await run_turn(client, messages, session, openai_tools)
        print(f"Agent: {answer}\n")


async def async_main():
    server_params = StdioServerParameters(command="python", args=[SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools
            openai_tools = mcp_to_openai_tools(mcp_tools)
            mcp_tools_map = {t.name: t for t in mcp_tools}

            print(f"Connected to RAG MCP server. {len(mcp_tools)} tools available.")
            await agent_loop(session, openai_tools, mcp_tools_map)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
