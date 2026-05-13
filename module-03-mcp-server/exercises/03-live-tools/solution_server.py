"""
Exercise 03 — Live Tools Server (solution)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Live Tools")

NOTES_DIR = Path(__file__).parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)


@server.tool()
def fetch_url(url: str) -> str:
    """Fetch a web page and return its text content (HTML stripped)."""
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        text = re.sub(r"<[^>]+>", "", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:5000]
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def save_note(filename: str, content: str) -> str:
    """Save a text note to the notes directory."""
    if ".." in filename or "/" in filename:
        return json.dumps({"error": "Invalid filename"})
    (NOTES_DIR / filename).write_text(content)
    return json.dumps({"saved": filename, "bytes": len(content)})


@server.tool()
def list_notes() -> str:
    """List all saved notes."""
    files = [f.name for f in NOTES_DIR.iterdir() if f.is_file()]
    return json.dumps(sorted(files))


@server.tool()
def read_note(filename: str) -> str:
    """Read a saved note by filename."""
    if ".." in filename or "/" in filename:
        return json.dumps({"error": "Invalid filename"})
    path = NOTES_DIR / filename
    if not path.exists():
        return json.dumps({"error": f"Note not found: {filename}"})
    return path.read_text()


if __name__ == "__main__":
    server.run()
