"""
Exercise 3: RAG MCP Server -- start.py
========================================
Console agent that connects to the RAG MCP server and chats using tool calling.

Run:  python start.py
"""

import asyncio
import json

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SERVER_SCRIPT = "server.py"


def mcp_to_openai_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to OpenAI function tools.

    Each MCP tool has .name, .description, .input_schema.
    Return a list of {"type": "function", "name", "description", "parameters"} dicts.
    """
    raise NotImplementedError


async def run_turn(client, messages, session, openai_tools, max_steps: int = 10) -> str:
    """Execute one conversational turn: call the LLM, handle tool calls, return final text.

    Loop up to max_steps times:
      1. Call client.responses.create with input=messages and tools=...
      2. calls = [item for item in response.output if item.type == "function_call"]
         If there are no calls, append the assistant message and return response.output_text.
      3. Otherwise, extend messages with response.output, then for each call:
         - Parse call.arguments, call session.call_tool(), append a
           {"type": "function_call_output", "call_id": call.call_id, "output": text} item.
    """
    raise NotImplementedError


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
