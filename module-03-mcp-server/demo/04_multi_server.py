"""Part 4: One agent, two MCP servers.

Requires http_server.py in another terminal, and OPENAI_API_KEY.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SHIP_SERVER_SCRIPT = str(Path(__file__).parent / "local_server.py")
NAV_SERVER_URL = "http://127.0.0.1:8000/mcp"


def log(tag: str, message: str):
    print(f"  [{tag}] {message}")


async def demo_multi_server_agent():
    print("=" * 60)
    print("PART 4: MULTI-SERVER AGENT")
    print("=" * 60)
    print()

    print("  Wiring BOTH servers into one agent. The LLM sees all 6 tools.")
    print("  Ship server (stdio) + Navigation server (HTTP).")
    print("  (Make sure http_server.py is running in another terminal)\n")

    server_params = StdioServerParameters(command=sys.executable, args=[SHIP_SERVER_SCRIPT])

    async with stdio_client(server_params) as (stdio_read, stdio_write):
        async with ClientSession(stdio_read, stdio_write) as ship_session:
            await ship_session.initialize()

            async with streamable_http_client(NAV_SERVER_URL) as (http_read, http_write):
                async with ClientSession(http_read, http_write) as nav_session:
                    await nav_session.initialize()
                    await _run_agent_loop(ship_session, nav_session)


async def _run_agent_loop(ship_session: ClientSession, nav_session: ClientSession):
    log("discovery", "Connecting to both servers...\n")

    ship_tools_raw = (await ship_session.list_tools()).tools
    nav_tools_raw = (await nav_session.list_tools()).tools
    ship_names = {tool.name for tool in ship_tools_raw}

    tool_router: dict[str, ClientSession] = {}
    openai_tools = []

    for tool in ship_tools_raw:
        tool_router[tool.name] = ship_session
        openai_tools.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        })
        log("discovery", f"  [ship/stdio]  {tool.name}: {tool.description}")

    for tool in nav_tools_raw:
        tool_router[tool.name] = nav_session
        openai_tools.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        })
        log("discovery", f"  [nav/http]    {tool.name}: {tool.description}")

    log("discovery", f"\n  Total: {len(openai_tools)} tools from 2 servers\n")

    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. You have access to ship crew/status "
                "tools AND navigation tools. Use them to answer queries. Be concise."
            ),
        },
    ]

    print("  Chat with the multi-server agent. Type 'quit' to exit.\n")

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        log("user", user_msg)

        for _ in range(10):
            log("llm request", f"Sending {len(messages)} messages, {len(openai_tools)} tools")

            response = client.responses.create(
                model=MODEL, reasoning={"effort": "none"}, input=messages, tools=openai_tools
            )
            calls = [item for item in response.output if item.type == "function_call"]
            log("llm response", f"output items: {[item.type for item in response.output]}")

            if calls:
                log("llm response", f"  {len(calls)} tool call(s) requested")
                messages += response.output

                for tc in calls:
                    name = tc.name
                    args = json.loads(tc.arguments)
                    session = tool_router[name]
                    source = "ship/stdio" if name in ship_names else "nav/http"

                    log("tool call", f"[{source}] {name}({json.dumps(args)})")
                    tool_result = await session.call_tool(name, args)
                    text = tool_result.content[0].text if tool_result.content else ""
                    log("tool result", f"[{source}] {text[:200]}")

                    messages.append({
                        "type": "function_call_output",
                        "call_id": tc.call_id,
                        "output": text,
                    })

            elif response.output_text:
                messages.append({"role": "assistant", "content": response.output_text})
                log("assistant", response.output_text)
                print()
                break
            else:
                log("assistant", "(no response)")
                print()
                break

    print("\n  Key points:")
    print("  - One agent, multiple MCP servers, mixed transports")
    print("  - Tool router maps each tool name to the right session")
    print("  - The LLM doesn't know or care which transport a tool uses")
    print("  - This is the real pattern: compose capabilities from many sources")
