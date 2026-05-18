"""
Module 3 Demo — Test the MCP Server
Connects to server.py, discovers tools, and calls each one. No LLM involved.

Run:  python test_server.py
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    server_script = str(Path(__file__).parent / "local_server.py")

    print("=" * 60)
    print("  MCP Server Test — discover tools and call them manually")
    print("=" * 60)

    print(f"\n  Connecting to: {server_script}\n")

    server_params = StdioServerParameters(
        command=sys.executable, args=[server_script]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ----- Tool discovery -----
            result = await session.list_tools()
            tools = result.tools

            print(f"  Discovered {len(tools)} tools:\n")
            for tool in tools:
                print(f"  {tool.name}")
                print(f"    description: {tool.description}")
                print(f"    inputSchema: {json.dumps(tool.inputSchema, indent=6)}")
                print()

            # ----- Call each tool -----
            print("-" * 60)
            print("  Calling each tool manually:\n")

            test_calls = [
                ("get_crew_count", {"department": "science"}),
                ("get_ship_status", {"system": "sensors"}),
                ("search_crew", {"query": "Chen"}),
            ]

            for name, args in test_calls:
                print(f"  → {name}({json.dumps(args)})")
                result = await session.call_tool(name, args)
                text = result.content[0].text if result.content else "(no content)"
                print(f"    ← {text}\n")

    print("=" * 60)
    print("  All tools working. Ready to connect an LLM.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
