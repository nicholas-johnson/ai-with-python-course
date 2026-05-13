"""Tests for Exercise 04 — MCP Client."""

from __future__ import annotations

import pytest

from start import MCPClient

SAMPLE_TOOLS = [
    {
        "name": "read_sensor",
        "description": "Read a ship sensor",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sensor_id": {"type": "string"},
            },
            "required": ["sensor_id"],
        },
    },
    {
        "name": "ship_time",
        "description": "Get current ship time",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def fake_call(name, arguments):
    if name == "read_sensor":
        return f"Sensor {arguments['sensor_id']}: 42.0"
    if name == "ship_time":
        return "Stardate 2347.078"
    raise ValueError(f"Unknown tool: {name}")


class TestDiscoverTools:
    def test_returns_all_tool_schemas(self):
        client = MCPClient(SAMPLE_TOOLS, fake_call)
        tools = client.discover_tools()
        assert "read_sensor" in tools
        assert "ship_time" in tools

    def test_schema_contains_properties(self):
        client = MCPClient(SAMPLE_TOOLS, fake_call)
        schema = client.discover_tools()["read_sensor"]
        assert "properties" in schema
        assert "sensor_id" in schema["properties"]


class TestCallTool:
    def test_successful_call(self):
        client = MCPClient(SAMPLE_TOOLS, fake_call)
        result = client.call_tool("read_sensor", {"sensor_id": "TEMP-01"})
        assert "result" in result
        assert "TEMP-01" in result["result"]

    def test_unknown_tool_returns_error(self):
        client = MCPClient(SAMPLE_TOOLS, fake_call)
        result = client.call_tool("nonexistent", {})
        assert "error" in result
        assert "Unknown" in result["error"] or "unknown" in result["error"].lower()

    def test_missing_required_arg_returns_error(self):
        client = MCPClient(SAMPLE_TOOLS, fake_call)
        result = client.call_tool("read_sensor", {})
        assert "error" in result
        assert "sensor_id" in result["error"]

    def test_tool_with_no_required_args(self):
        client = MCPClient(SAMPLE_TOOLS, fake_call)
        result = client.call_tool("ship_time", {})
        assert "result" in result
        assert "2347" in result["result"]

    def test_call_fn_exception_returns_error(self):
        def broken_call(name, args):
            raise RuntimeError("Connection lost")

        client = MCPClient(SAMPLE_TOOLS, broken_call)
        result = client.call_tool("ship_time", {})
        assert "error" in result
        assert "Connection lost" in result["error"]
