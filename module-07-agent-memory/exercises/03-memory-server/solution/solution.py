"""
Exercise 03 — Memory MCP Server (solution)
=============================================
Console agent connected to the Memory MCP server via stdio.

Run:  python solution.py
"""

import asyncio
import json

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SERVER_SCRIPT = "solution_server.py"


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


async def run_turn(client, messages, session, openai_tools, max_steps: int = 10) -> str:
    """Execute one conversational turn: call the LLM, handle tool calls, return final text."""
    for _ in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=openai_tools,
        )
        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            answer = choice.message.content or ""
            messages.append({"role": "assistant", "content": answer})
            return answer

        messages.append(choice.message)
        for tc in choice.message.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            print(f"  [tool_call] {fn_name}({json.dumps(fn_args)})")

            result = await session.call_tool(fn_name, fn_args)
            result_text = result.content[0].text if result.content else "No result"
            print(f"  [tool_result] {result_text[:150].replace(chr(10), ' ')}...")

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})

    return "(max tool steps reached)"


async def agent_loop(session, openai_tools, mcp_tools_map):
    """Interactive REPL: read user input, dispatch to run_turn."""
    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are BARKEEP, the AI bartender at The Nebula's Edge cantina "
                "on Relay Station Omicron. You have access to a memory system. "
                "Use the remember tool to store facts patrons share with you "
                "(drink orders, dietary restrictions, names, stories, preferences). "
                "Use the recall tool to retrieve memories when a patron asks "
                "'what's my usual?' or you need context. "
                "Use list_memories to see everything you know about your regulars. "
                "Always check your memories before claiming you don't know something. "
                "When you store a memory, use a descriptive snake_case key like "
                "drink_order_zara or allergy_tanaka. "
                "You're warm, slightly wry, and take pride in never forgetting a regular."
            ),
        }
    ]

    print("Type a message, /tools to list tools, or 'quit' to exit.\n")

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

            print(f"Connected to Cantina Memory server. {len(mcp_tools)} tools available.")
            await agent_loop(session, openai_tools, mcp_tools_map)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
