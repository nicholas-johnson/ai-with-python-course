"""
Exercise 2: MCP Research Tools Server -- SOLUTION
"""

import re
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Research Tools")

NOTES_DIR = Path(__file__).parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)


HEADERS = {"User-Agent": "ResearchAssistant/1.0 (educational project)"}


@mcp.tool()
async def fetch_url(url: str) -> str:
    """Fetch a web page and return its text content (HTML stripped)."""
    async with httpx.AsyncClient(headers=HEADERS) as client:
        resp = await client.get(url, follow_redirects=True, timeout=15)
        resp.raise_for_status()
    text = re.sub(r"<[^>]+>", " ", resp.text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:5000]


def _safe_filename(title: str) -> str:
    name = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    return name[:100] + ".md"


@mcp.tool()
async def save_note(title: str, content: str) -> str:
    """Save a research note to the notes directory."""
    path = NOTES_DIR / _safe_filename(title)
    path.write_text(f"# {title}\n\n{content}", encoding="utf-8")
    return f"Saved note: {title}"


@mcp.tool()
async def list_notes() -> str:
    """List all saved research notes."""
    notes = sorted(NOTES_DIR.glob("*.md"))
    if not notes:
        return "No notes saved yet."
    return "\n".join(f"- {n.stem.replace('_', ' ')}" for n in notes)


@mcp.tool()
async def read_note(title: str) -> str:
    """Read a saved research note by title."""
    path = NOTES_DIR / _safe_filename(title)
    if not path.exists():
        return f"Note not found: {title}"
    return path.read_text(encoding="utf-8")


@mcp.tool()
async def search_notes(query: str) -> str:
    """Search notes for a keyword. Returns matching note titles and excerpts."""
    results = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        if query.lower() in content.lower():
            excerpt = content[:200].replace("\n", " ")
            results.append(f"- {path.stem.replace('_', ' ')}: {excerpt}...")
    if not results:
        return f"No notes matching '{query}'."
    return "\n".join(results)


if __name__ == "__main__":
    mcp.run()
