"""
Module 3 Demo — MCP Server
Run:  python module-03-mcp-server/demo/demo.py

Three-part demo:
  Part 1: Explore the ship server (stdio transport)
  Part 2: Explore the navigation server (HTTP transport)
  Part 3: Hook BOTH servers to one LLM agent, with verbose logging

Requires:
  - OPENAI_API_KEY environment variable (Part 3 only)
  - http_server.py running in another terminal (Parts 2 and 3):
      python http_server.py
"""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

MODEL = "gpt-4o-mini"
SHIP_SERVER_SCRIPT = str(Path(__file__).parent / "local_server.py")
NAV_SERVER_URL = "http://localhost:8000/mcp"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")
    

def log(tag: str, message: str):
    print(f"  [{tag}] {message}")


async def discover_and_print(session: ClientSession, server_name: str):
    """Discover tools from a session and print them. Returns the tool list."""
    result = await session.list_tools()
    tools = result.tools
    log("discovery", f"{server_name} advertises {len(tools)} tools:")
    for tool in tools:
        params = tool.inputSchema.get("properties", {})
        required = tool.inputSchema.get("required", [])
        log("discovery", f"  {tool.name}: {tool.description}")
        log("discovery", f"    params={list(params.keys())}  required={required}")
    print()
    return tools


async def call_and_print(session: ClientSession, name: str, args: dict):
    """Call a tool and print the result."""
    log("tool call", f"{name}({json.dumps(args)})")
    result = await session.call_tool(name, args)
    text = result.content[0].text if result.content else "(no content)"
    parsed = json.loads(text)
    log("tool result", json.dumps(parsed, indent=4))
    print()
    return text


# ---------------------------------------------------------------------------
# Part 1: Explore the ship server (stdio)
# ---------------------------------------------------------------------------


async def demo_explore_stdio():
    section("Part 1: Explore the Ship Server (stdio)")

    print("  server.py is a FastMCP server with crew and ship tools.")
    print("  Transport: stdio — we spawn it as a subprocess.\n")

    server_params = StdioServerParameters(
        command=sys.executable, args=[SHIP_SERVER_SCRIPT]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await discover_and_print(session, "Pathfinder Ship")
            pause()

            print("  Calling each tool manually:\n")
            await call_and_print(session, "get_crew_count", {"department": "science"})
            await call_and_print(session, "get_ship_status", {"system": "sensors"})
            await call_and_print(session, "search_crew", {"query": "Chen"})

    print("  Key points:")
    print("  - stdio: server runs as a child process, talks over stdin/stdout")
    print("  - This is how Cursor and Claude Desktop connect to MCP servers")
    print("  - No port, no URL — the client spawns and manages the process")


# ---------------------------------------------------------------------------
# Part 2: Explore the navigation server (HTTP)
# ---------------------------------------------------------------------------


async def demo_explore_http():
    section("Part 2: Explore the Navigation Server (HTTP)")

    print("  http_server.py is a FastMCP server with navigation tools.")
    print(f"  Transport: Streamable HTTP at {NAV_SERVER_URL}")
    print("  (Make sure it's running in another terminal: python http_server.py)\n")

    async with streamablehttp_client(NAV_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await discover_and_print(session, "Pathfinder Navigation")
            pause()

            print("  Calling each tool manually:\n")
            await call_and_print(session, "get_coordinates", {"location": "proxima"})
            await call_and_print(session, "plot_course", {"origin": "earth", "destination": "proxima"})
            await call_and_print(session, "nearby_objects", {"sector": "Alpha-1", "radius": 5.0})

    print("  Key points:")
    print("  - HTTP: server runs independently at a URL, like any web service")
    print("  - Same protocol (JSON-RPC), same tool schemas — different transport")
    print("  - For remote servers, shared team tools, cloud deployment")
    print(f"  - One-line change: server.run(transport='streamable-http')")


# ---------------------------------------------------------------------------
# Part 3: Hook BOTH to the LLM
# ---------------------------------------------------------------------------


async def demo_multi_server_agent():
    section("Part 3: Multi-Server LLM Agent")

    print("  Wiring BOTH servers into one agent. The LLM sees all 6 tools.")
    print("  Ship server (stdio) + Navigation server (HTTP).")
    print("  (Make sure http_server.py is running in another terminal)\n")

    server_params = StdioServerParameters(
        command=sys.executable, args=[SHIP_SERVER_SCRIPT]
    )

    async with stdio_client(server_params) as (stdio_read, stdio_write):
        async with ClientSession(stdio_read, stdio_write) as ship_session:
            await ship_session.initialize()

            async with streamablehttp_client(NAV_SERVER_URL) as (http_read, http_write, _):
                async with ClientSession(http_read, http_write) as nav_session:
                    await nav_session.initialize()

                    await _run_agent_loop(ship_session, nav_session)


async def _run_agent_loop(ship_session: ClientSession, nav_session: ClientSession):
    # ----- Discovery from both servers -----
    log("discovery", "Connecting to both servers...\n")

    ship_tools_raw = (await ship_session.list_tools()).tools
    nav_tools_raw = (await nav_session.list_tools()).tools

    tool_router: dict[str, ClientSession] = {}
    openai_tools = []

    for tool in ship_tools_raw:
        tool_router[tool.name] = ship_session
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        })
        log("discovery", f"  [ship/stdio]  {tool.name}: {tool.description}")

    for tool in nav_tools_raw:
        tool_router[tool.name] = nav_session
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        })
        log("discovery", f"  [nav/http]    {tool.name}: {tool.description}")

    log("discovery", f"\n  Total: {len(openai_tools)} tools from 2 servers\n")

    # ----- Chat loop -----
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

            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=openai_tools
            )
            choice = response.choices[0]
            msg = choice.message

            log("llm response", f"finish_reason={choice.finish_reason}")

            if msg.tool_calls:
                log("llm response", f"  {len(msg.tool_calls)} tool call(s) requested")
                messages.append(msg)

                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    session = tool_router[name]
                    source = "ship/stdio" if session is not None and name in [t.name for t in ship_tools_raw] else "nav/http"

                    log("tool call", f"[{source}] {name}({json.dumps(args)})")
                    tool_result = await session.call_tool(name, args)
                    text = tool_result.content[0].text if tool_result.content else ""
                    log("tool result", f"[{source}] {text[:200]}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": text,
                    })

            elif msg.content:
                messages.append({"role": "assistant", "content": msg.content})
                log("assistant", msg.content)
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Explore ship server (stdio)",     demo_explore_stdio),
    "2": ("Explore navigation server (HTTP)", demo_explore_http),
    "3": ("Multi-server LLM agent",           demo_multi_server_agent),
}


async def main():
    print("\n" + "=" * 60)
    print("  MODULE 3 DEMO — MCP SERVER")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print(f"  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            await fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. stdio transport  — Cursor spawns a subprocess, no URL needed")
    print("  2. HTTP transport   — server at a URL, remote-friendly")
    print("  3. Multi-server     — one LLM, many MCP servers, mixed transports")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
