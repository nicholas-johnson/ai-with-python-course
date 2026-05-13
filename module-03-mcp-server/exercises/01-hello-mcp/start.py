"""
Exercise 01 — Hello MCP
Build a minimal MCP server with two tools.
"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("Hello Pathfinder")


# TODO: Register a 'greet' tool
# - Takes a 'name' parameter (str, default "Engineer")
# - Returns: "Welcome aboard, {name}. The DSS Pathfinder awaits."


# TODO: Register a 'ship_time' tool
# - Takes no parameters
# - Returns: "Stardate 2347.078 — 0800 hours shipboard time."
