"""
Module 3 Demo — Test the TV Ratings MCP Server
Connects to tv_server.py, discovers tools, and calls get_show_rating.

Run:  python test_tv_server.py
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    server_script = str(Path(__file__).parent / "tv_server.py")

    print("=" * 60)
    print("  TV Ratings MCP Server Test — discover tools and call them")
    print("=" * 60)

    print(f"\n  Connecting to: {server_script}\n")

    server_params = StdioServerParameters(command=sys.executable, args=[server_script])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.list_tools()
            tools = result.tools

            print(f"  Discovered {len(tools)} tools:\n")
            for tool in tools:
                print(f"  {tool.name}")
                print(f"    description: {tool.description}")
                print(f"    input_schema: {json.dumps(tool.input_schema, indent=6)}")
                print()

            print("-" * 60)
            print("  Calling get_show_rating:\n")

            test_calls = [
                ("get_show_rating", {"title": "Breaking Bad"}),
                ("get_show_rating", {"title": "The Office"}),
            ]

            failed = False
            for name, args in test_calls:
                print(f"  → {name}({json.dumps(args)})")
                result = await session.call_tool(name, args)
                text = result.content[0].text if result.content else "(no content)"
                parsed = json.loads(text)
                print(f"    ← {json.dumps(parsed, indent=4)}\n")
                if "error" in parsed:
                    failed = True

    print("=" * 60)
    if failed:
        print("  TV ratings tool returned an error.")
        raise SystemExit(1)
    print("  TV ratings tool working.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
