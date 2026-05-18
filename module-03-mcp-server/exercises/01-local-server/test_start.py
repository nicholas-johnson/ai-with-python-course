"""Tests for Exercise 01 — Local MCP Server: Power Grid."""

import json
import os
import sys
from pathlib import Path

import pytest

target = os.environ.get("TEST_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent / target))
from server import server as mcp_server


class TestGetPowerStatus:
    @pytest.mark.asyncio
    async def test_known_module(self):
        result = await mcp_server._tool_manager.call_tool("get_power_status", {"module": "habitat"})
        data = json.loads(result)
        assert data["module"] == "habitat"
        assert "power_level" in data
        assert "capacity" in data
        assert "load" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_unknown_module(self):
        result = await mcp_server._tool_manager.call_tool("get_power_status", {"module": "nonexistent"})
        data = json.loads(result)
        assert "error" in data


class TestAllocatePower:
    @pytest.mark.asyncio
    async def test_valid_transfer(self):
        result = await mcp_server._tool_manager.call_tool(
            "allocate_power", {"source": "habitat", "target": "docking", "amount": 50}
        )
        data = json.loads(result)
        assert data["success"] is True
        assert data["transferred"] == 50

    @pytest.mark.asyncio
    async def test_insufficient_power(self):
        result = await mcp_server._tool_manager.call_tool(
            "allocate_power", {"source": "docking", "target": "habitat", "amount": 99999}
        )
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_exceeds_capacity(self):
        result = await mcp_server._tool_manager.call_tool(
            "allocate_power", {"source": "habitat", "target": "comms", "amount": 100}
        )
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_unknown_module(self):
        result = await mcp_server._tool_manager.call_tool(
            "allocate_power", {"source": "fake", "target": "habitat", "amount": 10}
        )
        data = json.loads(result)
        assert "error" in data


class TestListAlerts:
    @pytest.mark.asyncio
    async def test_returns_alerts(self):
        result = await mcp_server._tool_manager.call_tool("list_alerts", {})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "severity" in data[0]
        assert "message" in data[0]


class TestToolDiscovery:
    def test_all_tools_registered(self):
        tools = mcp_server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "get_power_status" in names
        assert "allocate_power" in names
        assert "list_alerts" in names
