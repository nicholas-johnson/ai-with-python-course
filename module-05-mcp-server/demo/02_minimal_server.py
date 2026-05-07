"""
Demo: Minimal MCP server — one tool, stdio transport.
Run:  python module-05-mcp-server/demo/02_minimal_server.py

This starts an MCP server that exposes a single 'hello' tool.
Test it with an MCP client or the MCP inspector.
"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Hello Server")


@server.tool()
def hello(name: str = "Engineer") -> str:
    """Greet a crew member of the DSS Pathfinder."""
    return f"Welcome aboard the DSS Pathfinder, {name}. All systems nominal."


if __name__ == "__main__":
    print("Starting MCP server (stdio transport)...")
    print("Tools: hello")
    print("Press Ctrl+C to stop.\n")
    server.run()
