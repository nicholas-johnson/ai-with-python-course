"""
Exercise 3: RAG MCP Server -- server.py (delegates build)
===========================================================
A FastMCP server that wraps the RAG pipeline as discoverable tools.

Run standalone:  python -m mcp dev server.py
"""

from mcp.server.fastmcp import FastMCP

# TODO: Import from index_builder: load_logs, build_index, search
# TODO: Import from rag_utils: rag_chat

mcp = FastMCP("RAG Server")

# TODO: Build the index at module level
# logs = load_logs()
# collection = build_index(logs)


# TODO: Implement search_docs tool
# @mcp.tool()
# def search_docs(query: str, k: int = 5) -> str:
#     """Search the document index for relevant passages."""
#     hits = search(collection, query, k)
#     ... format hits as readable text ...


# TODO: Implement get_chunk tool
# @mcp.tool()
# def get_chunk(chunk_id: str) -> str:
#     """Retrieve the full text of a specific chunk by ID."""
#     ...


# TODO: Implement ask_docs tool
# @mcp.tool()
# def ask_docs(question: str) -> str:
#     """Ask a question and get a RAG-generated answer with citations."""
#     answer, passages = rag_chat(question, collection)
#     ...


# TODO: Implement list_sources tool
# @mcp.tool()
# def list_sources() -> str:
#     """List all source document IDs in the index."""
#     ...


if __name__ == "__main__":
    mcp.run()
