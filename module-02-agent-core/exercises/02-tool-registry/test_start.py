"""Tests for Exercise 02 — Tool Registry."""

import json

import pytest

from start import ToolRegistry, validate_required


@pytest.fixture()
def registry():
    reg = ToolRegistry()

    @reg.register(
        name="get_crew_count",
        description="Get crew count for a department",
        parameters={
            "type": "object",
            "properties": {
                "department": {"type": "string"},
            },
            "required": ["department"],
        },
    )
    def get_crew_count(department: str) -> dict:
        counts = {"science": 3, "engineering": 2}
        return {"department": department, "count": counts.get(department, 0)}

    @reg.register(
        name="ping",
        description="Simple ping",
        parameters={"type": "object", "properties": {}},
    )
    def ping() -> dict:
        return {"status": "pong"}

    return reg


class TestRegister:
    def test_decorator_returns_original_function(self):
        reg = ToolRegistry()
        @reg.register(name="f", description="d", parameters={})
        def my_func():
            return 42
        assert my_func() == 42

    def test_tool_stored_in_registry(self, registry):
        tools = registry.list_tools()
        names = [t["function"]["name"] for t in tools]
        assert "get_crew_count" in names
        assert "ping" in names


class TestListTools:
    def test_format(self, registry):
        tools = registry.list_tools()
        assert len(tools) == 2
        for tool in tools:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


class TestCall:
    def test_successful_call(self, registry):
        result = json.loads(registry.call("get_crew_count", {"department": "science"}))
        assert result == {"department": "science", "count": 3}

    def test_unknown_tool(self, registry):
        result = json.loads(registry.call("nonexistent", {}))
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_missing_required_field(self, registry):
        result = json.loads(registry.call("get_crew_count", {}))
        assert "error" in result
        assert "Missing required" in result["error"] or "department" in result["error"]

    def test_tool_that_raises(self):
        reg = ToolRegistry()

        @reg.register(name="broken", description="breaks", parameters={"type": "object", "properties": {}})
        def broken():
            raise ValueError("warp core breach")

        result = json.loads(reg.call("broken", {}))
        assert "error" in result
        assert "warp core breach" in result["error"]

    def test_no_args_tool(self, registry):
        result = json.loads(registry.call("ping", {}))
        assert result == {"status": "pong"}


class TestValidateRequired:
    def test_all_present(self):
        schema = {"required": ["a", "b"]}
        assert validate_required(schema, {"a": 1, "b": 2}) == []

    def test_missing_fields(self):
        schema = {"required": ["a", "b", "c"]}
        missing = validate_required(schema, {"a": 1})
        assert set(missing) == {"b", "c"}

    def test_no_required(self):
        schema = {"type": "object", "properties": {}}
        assert validate_required(schema, {}) == []
