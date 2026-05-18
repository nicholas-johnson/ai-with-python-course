"""Tests for Exercise 02 — HTTP MCP Server: Science Lab."""

import json
import os
import sys
from pathlib import Path

import pytest

target = os.environ.get("TEST_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent / target))
from server import server as mcp_server


class TestListExperiments:
    @pytest.mark.asyncio
    async def test_all_experiments(self):
        result = await mcp_server._tool_manager.call_tool("list_experiments", {})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 4

    @pytest.mark.asyncio
    async def test_filter_by_status(self):
        result = await mcp_server._tool_manager.call_tool("list_experiments", {"status": "running"})
        data = json.loads(result)
        assert all(e["status"] == "running" for e in data)
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_filter_no_match(self):
        result = await mcp_server._tool_manager.call_tool("list_experiments", {"status": "cancelled"})
        data = json.loads(result)
        assert data == []


class TestGetSample:
    @pytest.mark.asyncio
    async def test_known_sample(self):
        result = await mcp_server._tool_manager.call_tool("get_sample", {"sample_id": "S-101"})
        data = json.loads(result)
        assert data["sample_id"] == "S-101"
        assert data["type"] == "mineral"
        assert "origin" in data

    @pytest.mark.asyncio
    async def test_unknown_sample(self):
        result = await mcp_server._tool_manager.call_tool("get_sample", {"sample_id": "S-999"})
        data = json.loads(result)
        assert "error" in data


class TestRunAnalysis:
    @pytest.mark.asyncio
    async def test_valid_analysis(self):
        result = await mcp_server._tool_manager.call_tool(
            "run_analysis", {"sample_id": "S-101", "method": "spectral"}
        )
        data = json.loads(result)
        assert data["sample_id"] == "S-101"
        assert data["method"] == "spectral"
        assert "result" in data

    @pytest.mark.asyncio
    async def test_unknown_sample(self):
        result = await mcp_server._tool_manager.call_tool(
            "run_analysis", {"sample_id": "S-999", "method": "spectral"}
        )
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_unknown_method(self):
        result = await mcp_server._tool_manager.call_tool(
            "run_analysis", {"sample_id": "S-101", "method": "alchemy"}
        )
        data = json.loads(result)
        assert "error" in data


class TestToolDiscovery:
    def test_all_tools_registered(self):
        tools = mcp_server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "list_experiments" in names
        assert "get_sample" in names
        assert "run_analysis" in names
