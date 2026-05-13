"""Tests for Exercise 2: Tool-Calling Chat API"""

import importlib
import json
import subprocess
import sys
import time

import pytest
from fastapi.testclient import TestClient


def _load_app():
    for module_name in ("solution", "start"):
        try:
            mod = importlib.import_module(module_name)
            return mod.app
        except (ImportError, AttributeError):
            continue
    pytest.skip("No app found in solution.py or start.py")


def test_server_has_tools():
    """Check that the MCP server script defines tools."""
    for module_name in ("solution_server", "server"):
        try:
            mod = importlib.import_module(module_name)
            mcp = getattr(mod, "mcp", None)
            if mcp is not None:
                assert hasattr(mcp, "run"), "MCP server should be runnable"
                return
        except ImportError:
            continue
    pytest.skip("No MCP server module found")


def test_server_has_expected_tools():
    """Check that the MCP server defines the 5 expected tools."""
    for module_name in ("solution_server", "server"):
        try:
            mod = importlib.import_module(module_name)
            expected = {"fetch_url", "save_note", "list_notes", "read_note", "search_notes"}
            found = set()
            for name in dir(mod):
                if name in expected:
                    found.add(name)
            assert found == expected, f"Missing tools: {expected - found}"
            return
        except ImportError:
            continue
    pytest.skip("No MCP server module found")


def test_health():
    app = _load_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
