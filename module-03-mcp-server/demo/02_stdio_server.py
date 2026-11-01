"""Part 2: Explore the ship server over stdio."""

import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SHIP_SERVER_SCRIPT = str(Path(__file__).parent / "local_server.py")


def log(tag: str, message: str):
    print(f"  [{tag}] {message}")


async def discover_and_print(session: ClientSession, server_name: str):
    result = await session.list_tools()
    tools = result.tools
    log("discovery", f"{server_name} advertises {len(tools)} tools:")
    for tool in tools:
        params = tool.input_schema.get("properties", {})
        required = tool.input_schema.get("required", [])
        log("discovery", f"  {tool.name}: {tool.description}")
        log("discovery", f"    params={list(params.keys())}  required={required}")
    print()
    return tools


async def call_and_print(session: ClientSession, name: str, args: dict):
    log("tool call", f"{name}({json.dumps(args)})")
    result = await session.call_tool(name, args)
    text = result.content[0].text if result.content else "(no content)"
    parsed = json.loads(text)
    log("tool result", json.dumps(parsed, indent=4))
    print()
    return text


async def demo_explore_stdio():
    print("=" * 60)
    print("PART 2: SHIP SERVER (STDIO)")
    print("=" * 60)
    print()

    print("  local_server.py is an MCP server with crew and ship tools.")
    print("  Transport: stdio — we spawn it as a subprocess.\n")

    server_params = StdioServerParameters(command=sys.executable, args=[SHIP_SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await discover_and_print(session, "Pathfinder Ship")
            input("  [press Enter to continue]\n")

            print("  Calling each tool manually:\n")
            await call_and_print(session, "get_crew_count", {"department": "science"})
            await call_and_print(session, "get_ship_status", {"system": "sensors"})
            await call_and_print(session, "search_crew", {"query": "Chen"})

    print("  Key points:")
    print("  - stdio: server runs as a child process, talks over stdin/stdout")
    print("  - This is how Cursor and Claude Desktop connect to MCP servers")
    print("  - No port, no URL — the client spawns and manages the process")
