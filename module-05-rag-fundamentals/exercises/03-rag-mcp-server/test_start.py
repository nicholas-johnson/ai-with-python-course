"""Tests for Exercise 3: RAG MCP Server."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock


def _import_module(name: str):
    """Import a module from the exercise directory."""
    ex_dir = Path(__file__).resolve().parent
    mod_path = ex_dir / f"{name}.py"
    if not mod_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_server():
    """Import server.py (or solution_server.py as fallback)."""
    for name in ("server", "solution_server"):
        mod = _import_module(name)
        if mod and hasattr(mod, "mcp"):
            return mod
    raise FileNotFoundError("Neither server.py nor solution_server.py found with mcp")


def _import_client():
    """Import start.py (or solution.py as fallback)."""
    for name in ("start", "solution"):
        mod = _import_module(name)
        if mod:
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def test_server_has_expected_tools():
    """The MCP server should register search_docs, get_chunk, ask_docs, list_sources."""
    server = _import_server()
    tool_names = set()
    if hasattr(server.mcp, "_tool_manager"):
        for tool in server.mcp._tool_manager.list_tools():
            tool_names.add(tool.name)
    elif hasattr(server.mcp, "list_tools"):
        for tool in server.mcp.list_tools():
            tool_names.add(tool.name)

    expected = {"search_docs", "get_chunk", "ask_docs", "list_sources"}
    missing = expected - tool_names
    assert not missing, f"Missing tools: {missing}. Found: {tool_names}"


def test_mcp_to_openai_tools():
    """mcp_to_openai_tools converts MCP tools to OpenAI format."""
    client_mod = _import_client()
    if not hasattr(client_mod, "mcp_to_openai_tools"):
        return  # start.py doesn't have it yet

    mock_tool = MagicMock()
    mock_tool.name = "search_docs"
    mock_tool.description = "Search documents"
    mock_tool.inputSchema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    result = client_mod.mcp_to_openai_tools([mock_tool])
    assert len(result) == 1
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "search_docs"
    assert "parameters" in result[0]["function"]
