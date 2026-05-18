"""
Exercise 03: Memory MCP Server -- server.py
==============================================
A FastMCP server that wraps the memory system as discoverable tools.

Run standalone:  python -m mcp dev server.py
"""

from mcp.server.fastmcp import FastMCP

# TODO: Import from memory_store: LongTermMemory
# TODO: Import from summary: SmartSessionMemory

mcp = FastMCP("Cantina Memory")

# TODO: Create memory instances at module level
# long_term = LongTermMemory()
# session = SmartSessionMemory(max_turns=30, summarise_threshold=10)


# TODO: Implement remember tool
# @mcp.tool()
# def remember(key: str, value: str) -> str:
#     """Store a fact about a patron in long-term memory."""
#     long_term.remember(key, value)
#     return f"Remembered: {key} = {value}"


# TODO: Implement recall tool
# @mcp.tool()
# def recall(query: str) -> str:
#     """Recall memories matching a query prefix. Use empty string for all."""
#     entries = long_term.recall(prefix=query)
#     ... format entries as readable text ...


# TODO: Implement forget tool
# @mcp.tool()
# def forget(key: str) -> str:
#     """Forget a specific memory by key."""
#     if long_term.forget(key):
#         return f"Forgot: {key}"
#     return f"No memory found for: {key}"


# TODO: Implement list_memories tool
# @mcp.tool()
# def list_memories() -> str:
#     """List all active long-term memories with importance scores."""
#     entries = long_term.recall()
#     ... format all entries ...


# TODO: Implement get_summary tool
# @mcp.tool()
# def get_summary() -> str:
#     """Get the current conversation summary."""
#     summary = session.get_summary()
#     return summary if summary else "No conversation summary yet."


if __name__ == "__main__":
    mcp.run()
