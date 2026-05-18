"""Tests for Exercise 03 — Ship Documentation MCP Server."""

import json
import os
import sys
from pathlib import Path

import pytest

target = os.environ.get("TEST_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent / target))
from server import server as mcp_server


class TestSearchDocs:
    @pytest.mark.asyncio
    async def test_finds_match(self):
        result = await mcp_server._tool_manager.call_tool("search_docs", {"query": "evacuation"})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("emergency" in m["filename"] for m in data)

    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        result = await mcp_server._tool_manager.call_tool("search_docs", {"query": "WARP"})
        data = json.loads(result)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_no_match(self):
        result = await mcp_server._tool_manager.call_tool("search_docs", {"query": "xyznonexistent123"})
        data = json.loads(result)
        assert data == []


class TestListDocs:
    @pytest.mark.asyncio
    async def test_lists_all_docs(self):
        result = await mcp_server._tool_manager.call_tool("list_docs", {})
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 5
        filenames = {d["filename"] for d in data}
        assert "emergency-procedures" in filenames
        assert "navigation-manual" in filenames
        assert "crew-handbook" in filenames
        assert "engineering-guide" in filenames
        assert "medical-protocols" in filenames

    @pytest.mark.asyncio
    async def test_has_titles(self):
        result = await mcp_server._tool_manager.call_tool("list_docs", {})
        data = json.loads(result)
        for doc in data:
            assert "title" in doc
            assert len(doc["title"]) > 0


class TestReadDoc:
    @pytest.mark.asyncio
    async def test_known_doc(self):
        result = await mcp_server._tool_manager.call_tool("read_doc", {"filename": "crew-handbook"})
        assert "Crew Handbook" in result
        assert "Chain of Command" in result

    @pytest.mark.asyncio
    async def test_unknown_doc(self):
        result = await mcp_server._tool_manager.call_tool("read_doc", {"filename": "nonexistent"})
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_path_traversal_rejected(self):
        result = await mcp_server._tool_manager.call_tool("read_doc", {"filename": "../../etc/passwd"})
        data = json.loads(result)
        assert "error" in data


class TestResources:
    def test_index_resource_registered(self):
        resources = mcp_server._resource_manager.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "docs://index" in uris

    def test_doc_resources_registered(self):
        resources = mcp_server._resource_manager.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "docs://emergency-procedures" in uris
        assert "docs://navigation-manual" in uris
        assert "docs://crew-handbook" in uris

    @pytest.mark.asyncio
    async def test_index_contains_all_docs(self):
        resource = await mcp_server._resource_manager.get_resource("docs://index")
        text = await resource.read()
        assert "emergency-procedures" in text
        assert "navigation-manual" in text

    @pytest.mark.asyncio
    async def test_read_specific_doc(self):
        resource = await mcp_server._resource_manager.get_resource("docs://crew-handbook")
        text = await resource.read()
        assert "Crew Handbook" in text
        assert "Chain of Command" in text


class TestToolDiscovery:
    def test_all_tools_registered(self):
        tools = mcp_server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "search_docs" in names
        assert "read_doc" in names
        assert "list_docs" in names
