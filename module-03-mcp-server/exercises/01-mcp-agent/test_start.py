"""Tests for Exercise 01 — MCP Agent."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from mcp.types import TextContent

from server import server as mcp_server
from start import mcp_to_openai_tools


# ---- Server tool tests (via FastMCP internals) ----------------------------

def _extract(result) -> str:
    return result[0].text if isinstance(result[0], TextContent) else str(result[0])


class TestGetCrewCount:
    @pytest.mark.asyncio
    async def test_known_department(self):
        result = await mcp_server._tool_manager.call_tool("get_crew_count", {"department": "science"})
        data = json.loads(_extract(result))
        assert data["department"] == "science"
        assert data["count"] == 3

    @pytest.mark.asyncio
    async def test_unknown_department(self):
        result = await mcp_server._tool_manager.call_tool("get_crew_count", {"department": "catering"})
        data = json.loads(_extract(result))
        assert data["count"] == 0


class TestGetShipStatus:
    @pytest.mark.asyncio
    async def test_known_system(self):
        result = await mcp_server._tool_manager.call_tool("get_ship_status", {"system": "sensors"})
        data = json.loads(_extract(result))
        assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_unknown_system(self):
        result = await mcp_server._tool_manager.call_tool("get_ship_status", {"system": "hyperdrive"})
        data = json.loads(_extract(result))
        assert data["status"] == "unknown"


class TestSearchCrew:
    @pytest.mark.asyncio
    async def test_search_by_name(self):
        result = await mcp_server._tool_manager.call_tool("search_crew", {"query": "voss"})
        data = json.loads(_extract(result))
        assert len(data) >= 1
        assert any("Voss" in m["name"] for m in data)

    @pytest.mark.asyncio
    async def test_search_by_role(self):
        result = await mcp_server._tool_manager.call_tool("search_crew", {"query": "engineer"})
        data = json.loads(_extract(result))
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_no_match(self):
        result = await mcp_server._tool_manager.call_tool("search_crew", {"query": "zzzznotfound"})
        data = json.loads(_extract(result))
        assert data == []


class TestToolDiscovery:
    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        tools = await mcp_server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "get_crew_count" in names
        assert "get_ship_status" in names
        assert "search_crew" in names


# ---- mcp_to_openai_tools tests -------------------------------------------

class TestMcpToOpenaiTools:
    def test_converts_tools(self):
        fake_tools = [
            SimpleNamespace(
                name="my_tool",
                description="Does stuff",
                inputSchema={"type": "object", "properties": {"x": {"type": "string"}}},
            ),
        ]
        result = mcp_to_openai_tools(fake_tools)
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "my_tool"
        assert result[0]["function"]["description"] == "Does stuff"
        assert result[0]["function"]["parameters"]["type"] == "object"

    def test_handles_none_description(self):
        fake_tools = [
            SimpleNamespace(name="t", description=None, inputSchema={}),
        ]
        result = mcp_to_openai_tools(fake_tools)
        assert result[0]["function"]["description"] == ""

    def test_empty_list(self):
        assert mcp_to_openai_tools([]) == []
