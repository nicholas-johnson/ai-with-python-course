"""Tests for Exercise 02 — Ship Tools."""

import json

import pytest

from mcp.types import TextContent

from start import server


def extract_text(result) -> str:
    return result[0].text if isinstance(result[0], TextContent) else str(result[0])


class TestReadSensor:
    @pytest.mark.asyncio
    async def test_returns_sensor_data(self):
        result = await server._tool_manager.call_tool("read_sensor", {"sensor_id": "SEN-007"})
        data = json.loads(extract_text(result))
        assert data["sensor_id"] == "SEN-007"
        assert "value" in data
        assert "unit" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_deterministic_value(self):
        r1 = await server._tool_manager.call_tool("read_sensor", {"sensor_id": "SEN-001"})
        r2 = await server._tool_manager.call_tool("read_sensor", {"sensor_id": "SEN-001"})
        assert json.loads(extract_text(r1))["value"] == json.loads(extract_text(r2))["value"]


class TestQueryCrew:
    @pytest.mark.asyncio
    async def test_returns_all_crew(self):
        result = await server._tool_manager.call_tool("query_crew", {})
        data = json.loads(extract_text(result))
        assert len(data) > 0
        assert "id" in data[0]
        assert "name" in data[0]
        assert "role" in data[0]

    @pytest.mark.asyncio
    async def test_filter_by_department(self):
        result = await server._tool_manager.call_tool("query_crew", {"department": "science"})
        data = json.loads(extract_text(result))
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_unknown_department_returns_empty(self):
        result = await server._tool_manager.call_tool("query_crew", {"department": "nonexistent"})
        data = json.loads(extract_text(result))
        assert data == []


class TestSearchLogs:
    @pytest.mark.asyncio
    async def test_search_by_keyword(self):
        result = await server._tool_manager.call_tool("search_logs", {"query": "warp"})
        data = json.loads(extract_text(result))
        assert len(data) > 0
        assert all("warp" in log["content"].lower() for log in data)

    @pytest.mark.asyncio
    async def test_filter_by_category(self):
        result = await server._tool_manager.call_tool(
            "search_logs", {"query": "sensor", "category": "engineering"}
        )
        data = json.loads(extract_text(result))
        assert all(log["category"] == "engineering" for log in data)

    @pytest.mark.asyncio
    async def test_limit(self):
        result = await server._tool_manager.call_tool("search_logs", {"query": "the", "limit": 2})
        data = json.loads(extract_text(result))
        assert len(data) <= 2


class TestToolDiscovery:
    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        tools = await server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "read_sensor" in names
        assert "query_crew" in names
        assert "search_logs" in names
