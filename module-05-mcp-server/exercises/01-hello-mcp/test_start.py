"""Tests for Exercise 01 — Hello MCP."""

import pytest

from mcp.types import TextContent

from start import server


@pytest.fixture()
def mcp():
    return server._mcp_server


class TestGreetTool:
    @pytest.mark.asyncio
    async def test_greet_default_name(self):
        result = await server._tool_manager.call_tool("greet", {})
        assert len(result) > 0
        text = result[0].text if isinstance(result[0], TextContent) else str(result[0])
        assert "Engineer" in text
        assert "Pathfinder" in text

    @pytest.mark.asyncio
    async def test_greet_custom_name(self):
        result = await server._tool_manager.call_tool("greet", {"name": "Commander Voss"})
        text = result[0].text if isinstance(result[0], TextContent) else str(result[0])
        assert "Commander Voss" in text


class TestShipTimeTool:
    @pytest.mark.asyncio
    async def test_ship_time_returns_stardate(self):
        result = await server._tool_manager.call_tool("ship_time", {})
        text = result[0].text if isinstance(result[0], TextContent) else str(result[0])
        assert "2347" in text or "stardate" in text.lower()


class TestToolDiscovery:
    @pytest.mark.asyncio
    async def test_tools_are_registered(self):
        tools = await server._tool_manager.list_tools()
        names = [t.name for t in tools]
        assert "greet" in names
        assert "ship_time" in names

    @pytest.mark.asyncio
    async def test_greet_has_name_parameter(self):
        tools = await server._tool_manager.list_tools()
        greet_tool = next(t for t in tools if t.name == "greet")
        props = greet_tool.inputSchema.get("properties", {})
        assert "name" in props
