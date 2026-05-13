"""Tests for Exercise 02 — Data Tools."""

from __future__ import annotations

import json

import pytest
from mcp.types import TextContent

from server import server as mcp_server


def _extract(result) -> str:
    return result[0].text if isinstance(result[0], TextContent) else str(result[0])


class TestQueryCrew:
    @pytest.mark.asyncio
    async def test_returns_all_crew(self):
        result = await mcp_server._tool_manager.call_tool("query_crew", {})
        data = json.loads(_extract(result))
        assert len(data) > 0
        assert "name" in data[0]
        assert "role" in data[0]

    @pytest.mark.asyncio
    async def test_filter_by_department(self):
        result = await mcp_server._tool_manager.call_tool("query_crew", {"department": "science"})
        data = json.loads(_extract(result))
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_unknown_department_returns_empty(self):
        result = await mcp_server._tool_manager.call_tool("query_crew", {"department": "nonexistent"})
        data = json.loads(_extract(result))
        assert data == []


class TestSearchLogs:
    @pytest.mark.asyncio
    async def test_search_by_keyword(self):
        result = await mcp_server._tool_manager.call_tool("search_logs", {"keyword": "warp"})
        data = json.loads(_extract(result))
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_limit(self):
        result = await mcp_server._tool_manager.call_tool("search_logs", {"keyword": "the", "limit": 2})
        data = json.loads(_extract(result))
        assert len(data) <= 2


class TestReadSensor:
    @pytest.mark.asyncio
    async def test_returns_sensor_data(self):
        result = await mcp_server._tool_manager.call_tool("read_sensor", {"sensor_id": "SEN-007"})
        data = json.loads(_extract(result))
        assert data["sensor_id"] == "SEN-007"
        assert "value" in data
        assert "unit" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_deterministic(self):
        r1 = await mcp_server._tool_manager.call_tool("read_sensor", {"sensor_id": "SEN-001"})
        r2 = await mcp_server._tool_manager.call_tool("read_sensor", {"sensor_id": "SEN-001"})
        assert json.loads(_extract(r1))["value"] == json.loads(_extract(r2))["value"]


class TestListMissions:
    @pytest.mark.asyncio
    async def test_returns_missions(self):
        result = await mcp_server._tool_manager.call_tool("list_missions", {})
        data = json.loads(_extract(result))
        assert isinstance(data, list)
        assert len(data) > 0


class TestToolDiscovery:
    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        tools = await mcp_server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "query_crew" in names
        assert "search_logs" in names
        assert "read_sensor" in names
        assert "list_missions" in names
