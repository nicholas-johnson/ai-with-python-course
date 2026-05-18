"""
Exercise 03 — Ship Documentation MCP Server
Build a stdio FastMCP server that serves ship docs as MCP resources
and provides search/listing tools.

The docs/ folder contains markdown files that this server exposes.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

server = FastMCP("Ship Documentation")

DOCS_DIR = Path(__file__).parent.parent / "docs"


# ---------------------------------------------------------------------------
# Resources — TODO: implement these
# ---------------------------------------------------------------------------


@server.resource("docs://index")
def docs_index() -> str:
    """List all available ship documents."""
    # TODO: Read all .md files from DOCS_DIR
    # Return a formatted list of document names and their URIs
    # e.g. "- emergency-procedures (docs://emergency-procedures)\n..."
    raise NotImplementedError


# TODO: Add a resource for each document file
# Use @server.resource("docs://{filename}") pattern
# The resource should read the markdown file and return its contents
# Hint: iterate over DOCS_DIR.glob("*.md") and register a resource for each
# Or register them dynamically — one approach is to register a resource
# for each known filename.


# ---------------------------------------------------------------------------
# Tools — TODO: implement these
# ---------------------------------------------------------------------------


@server.tool()
def search_docs(query: str) -> str:
    """Search all ship documents for a keyword. Returns matching filenames and snippets."""
    # TODO: Search through all .md files in DOCS_DIR
    # For each file, check if query (case-insensitive) appears in the content
    # Return JSON list of matches, each with filename and a snippet (the matching line)
    raise NotImplementedError


@server.tool()
def read_doc(filename: str) -> str:
    """Read the full contents of a ship document by filename."""
    # TODO: Sanitise the filename (strip /, \, ..)
    # Build the path: DOCS_DIR / f"{filename}.md"
    # If the file exists, return its text content
    # If not, return JSON with an error message
    raise NotImplementedError


@server.tool()
def list_docs() -> str:
    """List all available ship document filenames and titles."""
    # TODO: Read all .md files from DOCS_DIR
    # Extract the title (first # heading) from each file
    # Return JSON list of {filename, title} objects
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server.run()
