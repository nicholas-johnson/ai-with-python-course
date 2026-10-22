"""
Exercise 03: Memory MCP Server -- solution_server.py
======================================================
Complete MCPServer server wrapping the memory system.

Run standalone:  mcp dev solution_server.py
"""

import sys

from mcp.server.mcpserver import MCPServer

from memory_store import LongTermMemory
from summary import SmartSessionMemory

mcp = MCPServer("Cantina Memory")

print("Cantina Memory: initialising memory systems...", file=sys.stderr, flush=True)
long_term = LongTermMemory()
session = SmartSessionMemory(max_turns=30, summarise_threshold=10)
print("Cantina Memory: ready", file=sys.stderr, flush=True)


@mcp.tool()
def remember(key: str, value: str) -> str:
    """Store a fact about a patron in long-term memory."""
    long_term.remember(key, value)
    return f"Remembered: {key} = {value}"


@mcp.tool()
def recall(query: str) -> str:
    """Recall memories matching a query prefix. Use empty string for all memories."""
    entries = long_term.recall(prefix=query)
    if not entries:
        return "No memories found" + (f" matching '{query}'" if query else "") + "."
    lines = []
    for key, entry in entries:
        lines.append(
            f"- {key}: {entry.value} (importance: {entry.importance:.2f})"
        )
    return "\n".join(lines)


@mcp.tool()
def forget(key: str) -> str:
    """Forget a specific memory by key."""
    if long_term.forget(key):
        return f"Forgot: {key}"
    return f"No memory found for: {key}"


@mcp.tool()
def list_memories() -> str:
    """List all active long-term memories with importance scores."""
    entries = long_term.recall()
    if not entries:
        return "No memories stored yet."
    lines = []
    for key, entry in entries:
        lines.append(
            f"- {key}: {entry.value} (importance: {entry.importance:.2f})"
        )
    return f"{len(entries)} memories:\n" + "\n".join(lines)


@mcp.tool()
def get_summary() -> str:
    """Get the current conversation summary."""
    summary = session.get_summary()
    return summary if summary else "No conversation summary yet."


if __name__ == "__main__":
    mcp.run()
