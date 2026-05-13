"""
Exercise 2: MCP Research Tools Server
======================================
Build an MCP server with 5 research tools:
  - fetch_url(url)       -- fetch a web page, strip HTML, return text
  - save_note(title, content) -- save a research note
  - list_notes()         -- list saved notes
  - read_note(title)     -- read a saved note
  - search_notes(query)  -- search notes by keyword

Run with:  python server.py
(Usually spawned by the FastAPI backend, not run directly.)
"""

from mcp.server.fastmcp import FastMCP

# TODO: import httpx, re, pathlib

mcp = FastMCP("Research Tools")

NOTES_DIR = None  # TODO: set to a Path for the notes/ directory


# TODO: Create the fetch_url tool
# @mcp.tool()
# async def fetch_url(url: str) -> str:
#     """Fetch a web page and return its text content."""
#     pass


# TODO: Create the save_note tool
# @mcp.tool()
# async def save_note(title: str, content: str) -> str:
#     """Save a research note."""
#     pass


# TODO: Create the list_notes tool
# @mcp.tool()
# async def list_notes() -> str:
#     """List all saved research notes."""
#     pass


# TODO: Create the read_note tool
# @mcp.tool()
# async def read_note(title: str) -> str:
#     """Read a saved research note by title."""
#     pass


# TODO: Create the search_notes tool
# @mcp.tool()
# async def search_notes(query: str) -> str:
#     """Search notes for a keyword."""
#     pass


if __name__ == "__main__":
    mcp.run()
