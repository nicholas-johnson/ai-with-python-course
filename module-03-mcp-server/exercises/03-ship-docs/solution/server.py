"""
Exercise 03 — Ship Documentation MCP Server (solution)
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

server = FastMCP("Ship Documentation")

DOCS_DIR = Path(__file__).parent.parent / "docs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_doc_files() -> list[Path]:
    return sorted(DOCS_DIR.glob("*.md"))


def _extract_title(path: Path) -> str:
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@server.resource("docs://index")
def docs_index() -> str:
    """List all available ship documents."""
    lines = []
    for f in _get_doc_files():
        name = f.stem
        title = _extract_title(f)
        lines.append(f"- {title} (docs://{name})")
    return "\n".join(lines)


for _doc_file in _get_doc_files():
    _name = _doc_file.stem

    def _make_reader(path: Path):
        @server.resource(f"docs://{path.stem}")
        def _read() -> str:
            return path.read_text()
        _read.__name__ = f"doc_{path.stem}"
        _read.__qualname__ = f"doc_{path.stem}"
        return _read

    _make_reader(_doc_file)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool()
def search_docs(query: str) -> str:
    """Search all ship documents for a keyword. Returns matching filenames and snippets."""
    q = query.lower()
    matches = []
    for f in _get_doc_files():
        content = f.read_text()
        for line in content.splitlines():
            if q in line.lower():
                matches.append({"filename": f.stem, "snippet": line.strip()})
                break
    return json.dumps(matches)


@server.tool()
def read_doc(filename: str) -> str:
    """Read the full contents of a ship document by filename."""
    safe = filename.replace("/", "").replace("\\", "").replace("..", "")
    path = DOCS_DIR / f"{safe}.md"
    if not path.exists():
        return json.dumps({"error": f"Unknown document: {filename}"})
    return path.read_text()


@server.tool()
def list_docs() -> str:
    """List all available ship document filenames and titles."""
    docs = []
    for f in _get_doc_files():
        docs.append({"filename": f.stem, "title": _extract_title(f)})
    return json.dumps(docs)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
