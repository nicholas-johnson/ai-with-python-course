"""Part 1: List the tools on the ship server, then return.
Run alone:  python module-03-mcp-server/demo/01_list_tools.py
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SHIP_SERVER_SCRIPT = str(Path(__file__).parent / "local_server.py")


async def demo_list_tools():
    print("=" * 60)
    print("PART 1: LIST TOOLS")
    print("=" * 60)
    print()

    server_params = StdioServerParameters(command=sys.executable, args=[SHIP_SERVER_SCRIPT])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            for tool in result.tools:
                print(f"  {tool.name}")
    print()


if __name__ == "__main__":
    asyncio.run(demo_list_tools())
