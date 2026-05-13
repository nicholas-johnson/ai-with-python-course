"""
Exercise 03 — Live Tools Server
MCP server with web fetch and file management tools.

Run directly:  python server.py
Used by:       start.py connects to this server automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Live Tools")

NOTES_DIR = Path(__file__).parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# TODO: Register four tools using @server.tool()
# ---------------------------------------------------------------------------

# TODO: fetch_url(url: str) -> str
#   Fetch the URL using httpx.get() (set a 10-second timeout).
#   Strip HTML tags with a simple regex or just return response.text truncated
#   to 5000 characters. Return the text content.
#   On error, return a JSON string with {"error": str(e)}.
#
#   Hint: import httpx, re
#         text = re.sub(r"<[^>]+>", "", response.text)


# TODO: save_note(filename: str, content: str) -> str
#   Save content to NOTES_DIR / filename.
#   Sanitise filename: reject if it contains ".." or "/".
#   Return JSON with {"saved": filename, "bytes": len(content)}.


# TODO: list_notes() -> str
#   List all files in NOTES_DIR.
#   Return JSON list of filenames.


# TODO: read_note(filename: str) -> str
#   Read NOTES_DIR / filename and return its contents.
#   Sanitise filename: reject if it contains ".." or "/".
#   If file doesn't exist, return JSON {"error": "Note not found: <filename>"}.


# ---------------------------------------------------------------------------
# Run as MCP server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
