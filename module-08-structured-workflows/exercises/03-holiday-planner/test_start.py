"""Tests for Exercise 03: Holiday Planner."""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _import_module(name: str):
    """Import a module from the exercise directory."""
    ex_dir = Path(__file__).resolve().parent
    mod_path = ex_dir / f"{name}.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"{name}.py not found")
    spec = importlib.util.spec_from_file_location(name, mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
    for name in ("start", "solution"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _import_server():
    """Import server.py (or solution_server.py as fallback)."""
    ex_dir = Path(__file__).resolve().parent
    for name in ("server", "solution_server"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("Neither server.py nor solution_server.py found")


# --- FastAPI endpoint tests ---

def test_health_endpoint():
    """GET /health returns status ok."""
    from fastapi.testclient import TestClient

    mod = _import_start()
    client = TestClient(mod.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_plan_endpoint():
    """POST /plan returns JSON with a plan."""
    from fastapi.testclient import TestClient

    mod = _import_start()
    test_client = TestClient(mod.app)

    plan_json = json.dumps({
        "steps": [
            {"step_number": 1, "description": "Research destination"},
            {"step_number": 2, "description": "Find flights"},
        ]
    })

    mock_message = MagicMock()
    mock_message.content = plan_json

    with patch.object(mod, "client") as mock_openai:
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )
        resp = test_client.post("/plan", json={"message": "Trip to Tokyo"})

    assert resp.status_code == 200
    data = resp.json()
    assert "plan" in data
    assert isinstance(data["plan"], list)
    assert len(data["plan"]) >= 1


# --- MCP server tool tests ---

def test_mcp_server_has_search_web():
    """MCP server defines a search_web tool."""
    mod = _import_server()
    assert hasattr(mod, "search_web"), "Server should define search_web"


def test_mcp_server_has_search_flights():
    """MCP server defines a search_flights tool."""
    mod = _import_server()
    assert hasattr(mod, "search_flights"), "Server should define search_flights"


def test_mcp_server_has_search_hotels():
    """MCP server defines a search_hotels tool."""
    mod = _import_server()
    assert hasattr(mod, "search_hotels"), "Server should define search_hotels"


def test_mcp_server_has_preferences():
    """MCP server defines remember_preference and recall_preferences tools."""
    mod = _import_server()
    assert hasattr(mod, "remember_preference"), "Server should define remember_preference"
    assert hasattr(mod, "recall_preferences"), "Server should define recall_preferences"


def test_search_flights_returns_results():
    """search_flights returns a string with flight information."""
    mod = _import_server()
    result = mod.search_flights("London", "Tokyo", "2025-04-15")
    assert isinstance(result, str)
    assert "London" in result or "Tokyo" in result
    assert "$" in result


def test_search_hotels_returns_results():
    """search_hotels returns a string with hotel information."""
    mod = _import_server()
    result = mod.search_hotels("Tokyo", "2025-04-15", "2025-04-22")
    assert isinstance(result, str)
    assert "Tokyo" in result
    assert "$" in result


def test_preferences_round_trip():
    """remember_preference stores and recall_preferences retrieves."""
    mod = _import_server()
    mod._preferences.clear()

    result = mod.remember_preference("budget", "moderate")
    assert "saved" in result.lower() or "budget" in result.lower()

    prefs = mod.recall_preferences()
    assert "budget" in prefs
    assert "moderate" in prefs

    mod._preferences.clear()
