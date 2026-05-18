"""Tests for Exercise 03 — Memory MCP Server (solution)."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock


def _import_module(name: str):
    """Import a module from this directory."""
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
    """Import solution_server.py."""
    mod = _import_module("solution_server")
    if mod and hasattr(mod, "mcp"):
        return mod
    raise FileNotFoundError("solution_server.py not found or missing mcp attribute")


def _import_client():
    """Import solution.py."""
    mod = _import_module("solution")
    if mod:
        return mod
    raise FileNotFoundError("solution.py not found")


def test_server_has_expected_tools():
    """The MCP server should register remember, recall, forget, list_memories, get_summary."""
    server = _import_server()
    tool_names = set()
    if hasattr(server.mcp, "_tool_manager"):
        for tool in server.mcp._tool_manager.list_tools():
            tool_names.add(tool.name)
    elif hasattr(server.mcp, "list_tools"):
        for tool in server.mcp.list_tools():
            tool_names.add(tool.name)

    expected = {"remember", "recall", "forget", "list_memories", "get_summary"}
    missing = expected - tool_names
    assert not missing, f"Missing tools: {missing}. Found: {tool_names}"


def test_mcp_to_openai_tools():
    """mcp_to_openai_tools converts MCP tools to OpenAI format."""
    client_mod = _import_client()
    if not hasattr(client_mod, "mcp_to_openai_tools"):
        return

    mock_tool = MagicMock()
    mock_tool.name = "remember"
    mock_tool.description = "Store a fact in long-term memory"
    mock_tool.inputSchema = {
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"},
        },
        "required": ["key", "value"],
    }

    result = client_mod.mcp_to_openai_tools([mock_tool])
    assert len(result) == 1
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "remember"
    assert "parameters" in result[0]["function"]


def test_client_has_main():
    """The client module should have a main function."""
    client_mod = _import_client()
    assert hasattr(client_mod, "main"), "Client module must have a main() function"


def test_server_has_mcp_instance():
    """The server module should have a FastMCP instance named 'mcp'."""
    server = _import_server()
    assert hasattr(server, "mcp"), "Server module must have an 'mcp' attribute"
