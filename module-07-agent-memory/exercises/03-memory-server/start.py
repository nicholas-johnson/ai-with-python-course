"""
Exercise 03 — Memory MCP Server
===============================
Console agent connected to the Cantina Memory server over stdio.

The model drives the memory tools. The harness drives the compaction tools:
it records every turn and compacts when the thread goes over budget.

Run:  python start.py
"""

import asyncio
import json  # noqa: F401 — you need this in run_turn
import os

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SERVER_SCRIPT = "server.py"

THREAD_ID = "tonight"
BUDGET_TOKENS = 500
PATRON = "zara"

SYSTEM_PROMPT = (
    "You are BARKEEP, the AI bartender at The Nebula's Edge cantina on Relay "
    "Station Omicron, serving " + PATRON + " tonight. "
    "Your memory lives behind tools, not in your head. "
    f"Call recall(patron='{PATRON}', query=...) before claiming you do not know "
    "something, and remember(...) when a patron tells you something durable: a "
    "usual order, an allergy, who they are, an unpaid tab. "
    "Do not store one-off questions or small talk. "
    "You are warm, slightly wry, and you never forget a regular."
)


def mcp_to_openai_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to OpenAI function tools.

    Each MCP tool has .name, .description, and .input_schema.
    """
    # TODO: return a list of
    #   {"type": "function", "name": ..., "description": ..., "parameters": ...}
    # where parameters is the tool's input_schema
    raise NotImplementedError("TODO")


async def call_text(session, name: str, arguments: dict) -> str:
    """Call one MCP tool and return its text content."""
    # TODO: result = await session.call_tool(name, arguments)
    #       return result.content[0].text, or "No result" when content is empty
    raise NotImplementedError("TODO")


async def run_turn(client, messages, session, openai_tools, max_steps: int = 10) -> str:
    """One conversational turn, including any tool calls the model makes."""
    # TODO: loop up to max_steps times:
    #   1. client.responses.create(model=MODEL, reasoning={"effort": "none"},
    #      input=messages, tools=openai_tools)
    #   2. calls = [item for item in response.output if item.type == "function_call"]
    #      With no calls: append the assistant message and return
    #      response.output_text.
    #   3. Otherwise extend messages with response.output, then for each call:
    #      parse call.arguments, run it through call_text, and append
    #      {"type": "function_call_output", "call_id": call.call_id,
    #       "output": result_text}
    #      Print the call and its result — watching the agent reach for memory
    #      is most of the point of this exercise.
    raise NotImplementedError("TODO")


async def record_and_compact(session, role: str, text: str) -> None:
    """Log a turn to the server, and compact the thread when it is over budget.

    This is harness work, not a decision for the model: the thread has to be
    recorded whatever the model chooses to do.
    """
    # TODO: 1. call append_turn with thread_id=THREAD_ID, role, text
    #       2. call thread_budget with THREAD_ID and BUDGET_TOKENS
    #       3. return if the verdict does not say "over budget"
    #       4. otherwise call compact_thread and print the first line of what
    #          comes back
    raise NotImplementedError("TODO")


async def agent_loop(session, openai_tools, mcp_tools_map):
    """Interactive REPL: read user input, dispatch to run_turn."""
    client = OpenAI()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Type a message, or /tools, /anchors, /budget, /thread, quit.\n")

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
                summary = (tool.description or "").strip().splitlines()[0]
                print(f"  - {name}: {summary}")
            print()
            continue

        if user_input == "/anchors":
            print(await call_text(session, "get_anchors", {"thread_id": THREAD_ID}) + "\n")
            continue

        if user_input == "/budget":
            print(
                await call_text(
                    session,
                    "thread_budget",
                    {"thread_id": THREAD_ID, "budget_tokens": BUDGET_TOKENS},
                )
                + "\n"
            )
            continue

        if user_input == "/thread":
            print(
                await call_text(
                    session, "compact_thread", {"thread_id": THREAD_ID, "budget_tokens": 0}
                )
                + "\n"
            )
            continue

        messages.append({"role": "user", "content": user_input})
        answer = await run_turn(client, messages, session, openai_tools)
        print(f"Agent: {answer}\n")

        await record_and_compact(session, "user", user_input)
        await record_and_compact(session, "assistant", answer)


async def async_main():
    server_params = StdioServerParameters(command="python", args=[SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools
            openai_tools = mcp_to_openai_tools(mcp_tools)
            mcp_tools_map = {tool.name: tool for tool in mcp_tools}

            print(f"Connected to Cantina Memory. {len(mcp_tools)} tools available.")
            await agent_loop(session, openai_tools, mcp_tools_map)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
