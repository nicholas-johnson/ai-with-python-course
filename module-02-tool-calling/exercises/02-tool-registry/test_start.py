"""Tests for Exercise 02 — Tool Registry."""

import json

import pytest

from start import ToolRegistry, registry


# ---------------------------------------------------------------------------
# ToolRegistry class tests
# ---------------------------------------------------------------------------

class TestRegisterDecorator:
    def test_decorator_returns_original_function(self):
        reg = ToolRegistry()

        @reg.register("test_fn", "A test", {"type": "object", "properties": {}})
        def my_func():
            return 42

        assert my_func() == 42

    def test_tool_appears_in_list(self):
        reg = ToolRegistry()

        @reg.register("greet", "Say hello", {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        })
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        tools = reg.list_tools()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "greet"


class TestListTools:
    def test_format_matches_openai(self):
        reg = ToolRegistry()

        @reg.register("ping", "Ping test", {"type": "object", "properties": {}})
        def ping() -> str:
            return "pong"

        tools = reg.list_tools()
        assert len(tools) == 1
        tool = tools[0]
        assert tool["type"] == "function"
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]

    def test_multiple_tools(self):
        reg = ToolRegistry()

        @reg.register("a", "Tool A", {"type": "object", "properties": {}})
        def tool_a() -> str:
            return "a"

        @reg.register("b", "Tool B", {"type": "object", "properties": {}})
        def tool_b() -> str:
            return "b"

        tools = reg.list_tools()
        names = {t["function"]["name"] for t in tools}
        assert names == {"a", "b"}


class TestExecute:
    def test_successful_call(self):
        reg = ToolRegistry()

        @reg.register("add", "Add numbers", {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        })
        def add(a: int, b: int) -> str:
            return json.dumps({"sum": a + b})

        result = json.loads(reg.execute("add", {"a": 3, "b": 4}))
        assert result == {"sum": 7}

    def test_unknown_tool_returns_error(self):
        reg = ToolRegistry()
        result = json.loads(reg.execute("nonexistent", {}))
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_handler_exception_caught(self):
        reg = ToolRegistry()

        @reg.register("boom", "Explodes", {"type": "object", "properties": {}})
        def boom() -> str:
            raise ValueError("warp core breach")

        result = json.loads(reg.execute("boom", {}))
        assert "error" in result
        assert "warp core breach" in result["error"]

    def test_non_string_result_serialized(self):
        reg = ToolRegistry()

        @reg.register("data", "Returns dict", {"type": "object", "properties": {}})
        def data() -> dict:
            return {"status": "ok"}

        result = json.loads(reg.execute("data", {}))
        assert result == {"status": "ok"}


# ---------------------------------------------------------------------------
# Module-level registry (registered tools)
# ---------------------------------------------------------------------------

class TestShipToolsRegistered:
    def test_three_tools_registered(self):
        tools = registry.list_tools()
        assert len(tools) == 3

    def test_tool_names(self):
        names = {t["function"]["name"] for t in registry.list_tools()}
        assert names == {"get_crew_count", "get_ship_status", "search_crew"}

    def test_get_crew_count_via_execute(self):
        result = json.loads(registry.execute("get_crew_count", {"department": "science"}))
        assert result["department"] == "science"
        assert isinstance(result["count"], int)
        assert result["count"] > 0

    def test_get_ship_status_via_execute(self):
        result = json.loads(registry.execute("get_ship_status", {"system": "warp"}))
        assert result["system"] == "warp"
        assert "status" in result

    def test_search_crew_via_execute(self):
        results = json.loads(registry.execute("search_crew", {"query": "Voss"}))
        assert len(results) >= 1
        assert any("Voss" in r["name"] for r in results)
