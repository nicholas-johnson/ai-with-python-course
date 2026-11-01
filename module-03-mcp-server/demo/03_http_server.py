"""Part 3: Explore the navigation server over HTTP.

Requires http_server.py in another terminal:
  python module-03-mcp-server/demo/http_server.py
"""

import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

NAV_SERVER_URL = "http://localhost:8000/mcp"


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


async def demo_explore_http():
    print("=" * 60)
    print("PART 3: NAVIGATION SERVER (HTTP)")
    print("=" * 60)
    print()

    print("  http_server.py is an MCP server with navigation tools.")
    print(f"  Transport: Streamable HTTP at {NAV_SERVER_URL}")
    print("  (Make sure it's running in another terminal: python http_server.py)\n")

    async with streamable_http_client(NAV_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await discover_and_print(session, "Pathfinder Navigation")
            input("  [press Enter to continue]\n")

            print("  Calling each tool manually:\n")
            await call_and_print(session, "get_coordinates", {"location": "proxima"})
            await call_and_print(
                session, "plot_course", {"origin": "earth", "destination": "proxima"}
            )
            await call_and_print(session, "nearby_objects", {"sector": "Alpha-1", "radius": 5.0})

    print("  Key points:")
    print("  - HTTP: server runs independently at a URL, like any web service")
    print("  - Same protocol (JSON-RPC), same tool schemas — different transport")
    print("  - For remote servers, shared team tools, cloud deployment")
    print("  - One-line change: server.run(transport='streamable-http')")
