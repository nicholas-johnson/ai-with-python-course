"""Tests for Exercise 03 — Live Tools."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from mcp.types import TextContent

from server import server as mcp_server, NOTES_DIR


def _extract(result) -> str:
    return result[0].text if isinstance(result[0], TextContent) else str(result[0])


@pytest.fixture(autouse=True)
def _clean_notes():
    """Remove notes dir before/after each test."""
    if NOTES_DIR.exists():
        shutil.rmtree(NOTES_DIR)
    NOTES_DIR.mkdir(exist_ok=True)
    yield
    if NOTES_DIR.exists():
        shutil.rmtree(NOTES_DIR)
    NOTES_DIR.mkdir(exist_ok=True)


class TestFetchUrl:
    @pytest.mark.asyncio
    async def test_bad_url_returns_error(self):
        result = await mcp_server._tool_manager.call_tool(
            "fetch_url", {"url": "http://localhost:1/nope"}
        )
        text = _extract(result)
        data = json.loads(text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_returns_string(self):
        result = await mcp_server._tool_manager.call_tool(
            "fetch_url", {"url": "http://localhost:1/nope"}
        )
        assert isinstance(_extract(result), str)


class TestSaveNote:
    @pytest.mark.asyncio
    async def test_save_and_verify(self):
        result = await mcp_server._tool_manager.call_tool(
            "save_note", {"filename": "test.txt", "content": "hello world"}
        )
        data = json.loads(_extract(result))
        assert data["saved"] == "test.txt"
        assert data["bytes"] == 11
        assert (NOTES_DIR / "test.txt").read_text() == "hello world"

    @pytest.mark.asyncio
    async def test_rejects_path_traversal(self):
        result = await mcp_server._tool_manager.call_tool(
            "save_note", {"filename": "../evil.txt", "content": "bad"}
        )
        data = json.loads(_extract(result))
        assert "error" in data

    @pytest.mark.asyncio
    async def test_rejects_slash(self):
        result = await mcp_server._tool_manager.call_tool(
            "save_note", {"filename": "sub/file.txt", "content": "bad"}
        )
        data = json.loads(_extract(result))
        assert "error" in data


class TestListNotes:
    @pytest.mark.asyncio
    async def test_empty_dir(self):
        result = await mcp_server._tool_manager.call_tool("list_notes", {})
        data = json.loads(_extract(result))
        assert data == []

    @pytest.mark.asyncio
    async def test_after_save(self):
        (NOTES_DIR / "a.txt").write_text("aaa")
        (NOTES_DIR / "b.txt").write_text("bbb")
        result = await mcp_server._tool_manager.call_tool("list_notes", {})
        data = json.loads(_extract(result))
        assert "a.txt" in data
        assert "b.txt" in data


class TestReadNote:
    @pytest.mark.asyncio
    async def test_read_existing(self):
        (NOTES_DIR / "memo.txt").write_text("remember this")
        result = await mcp_server._tool_manager.call_tool(
            "read_note", {"filename": "memo.txt"}
        )
        assert _extract(result) == "remember this"

    @pytest.mark.asyncio
    async def test_read_missing(self):
        result = await mcp_server._tool_manager.call_tool(
            "read_note", {"filename": "gone.txt"}
        )
        data = json.loads(_extract(result))
        assert "error" in data

    @pytest.mark.asyncio
    async def test_rejects_path_traversal(self):
        result = await mcp_server._tool_manager.call_tool(
            "read_note", {"filename": "../../etc/passwd"}
        )
        data = json.loads(_extract(result))
        assert "error" in data


class TestToolDiscovery:
    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        tools = await mcp_server._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "fetch_url" in names
        assert "save_note" in names
        assert "list_notes" in names
        assert "read_note" in names
