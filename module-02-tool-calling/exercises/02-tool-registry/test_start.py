"""Tests for Exercise 02 — Auto-Schema Tool Registry."""

import json

import pytest

from start import MISSION_LOG, ToolRegistry, registry


# ---------------------------------------------------------------------------
# ToolRegistry class tests
# ---------------------------------------------------------------------------


class TestRegisterDecorator:
    def test_decorator_returns_original_function(self):
        reg = ToolRegistry()

        @reg.register("A test tool")
        def my_func() -> str:
            return "42"

        assert my_func() == "42"

    def test_tool_name_from_function_name(self):
        reg = ToolRegistry()

        @reg.register("Say hello")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        tools = reg.list_tools()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "greet"


class TestAutoSchema:
    def test_string_param(self):
        reg = ToolRegistry()

        @reg.register("Echo a message")
        def echo(message: str) -> str:
            return message

        schema = reg.list_tools()[0]["function"]["parameters"]
        assert schema["properties"]["message"]["type"] == "string"
        assert "message" in schema["required"]

    def test_float_param(self):
        reg = ToolRegistry()

        @reg.register("Scale a value")
        def scale(factor: float) -> str:
            return str(factor)

        schema = reg.list_tools()[0]["function"]["parameters"]
        assert schema["properties"]["factor"]["type"] == "number"

    def test_int_param(self):
        reg = ToolRegistry()

        @reg.register("Repeat N times")
        def repeat(n: int) -> str:
            return str(n)

        schema = reg.list_tools()[0]["function"]["parameters"]
        assert schema["properties"]["n"]["type"] == "integer"

    def test_bool_param(self):
        reg = ToolRegistry()

        @reg.register("Toggle verbose")
        def toggle(verbose: bool) -> str:
            return str(verbose)

        schema = reg.list_tools()[0]["function"]["parameters"]
        assert schema["properties"]["verbose"]["type"] == "boolean"

    def test_multiple_params(self):
        reg = ToolRegistry()

        @reg.register("Check range")
        def check(atmosphere: str, gravity: float) -> str:
            return "ok"

        schema = reg.list_tools()[0]["function"]["parameters"]
        assert schema["properties"]["atmosphere"]["type"] == "string"
        assert schema["properties"]["gravity"]["type"] == "number"
        assert set(schema["required"]) == {"atmosphere", "gravity"}

    def test_optional_param_not_required(self):
        reg = ToolRegistry()

        @reg.register("Greet with optional title")
        def greet(name: str, title: str = "Dr.") -> str:
            return f"{title} {name}"

        schema = reg.list_tools()[0]["function"]["parameters"]
        assert "name" in schema["required"]
        assert "title" not in schema["required"]
        assert "title" in schema["properties"]


class TestListTools:
    def test_format_matches_openai(self):
        reg = ToolRegistry()

        @reg.register("Ping test")
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

        @reg.register("Tool A")
        def tool_a() -> str:
            return "a"

        @reg.register("Tool B")
        def tool_b() -> str:
            return "b"

        tools = reg.list_tools()
        names = {t["function"]["name"] for t in tools}
        assert names == {"tool_a", "tool_b"}


class TestExecute:
    def test_successful_call(self):
        reg = ToolRegistry()

        @reg.register("Add numbers")
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

        @reg.register("Explodes")
        def boom() -> str:
            raise ValueError("warp core breach")

        result = json.loads(reg.execute("boom", {}))
        assert "error" in result
        assert "warp core breach" in result["error"]

    def test_non_string_result_serialized(self):
        reg = ToolRegistry()

        @reg.register("Returns dict")
        def data() -> dict:
            return {"status": "ok"}

        result = json.loads(reg.execute("data", {}))
        assert result == {"status": "ok"}


# ---------------------------------------------------------------------------
# Module-level registry (planetary tools)
# ---------------------------------------------------------------------------


class TestPlanetaryToolsRegistered:
    def test_three_tools_registered(self):
        tools = registry.list_tools()
        assert len(tools) == 3

    def test_tool_names(self):
        names = {t["function"]["name"] for t in registry.list_tools()}
        assert names == {"scan_planet", "check_habitability", "log_discovery"}

    def test_scan_planet_known(self):
        result = json.loads(registry.execute("scan_planet", {"planet_id": "TRAP-1e"}))
        assert result["name"] == "TRAP-1e"
        assert "atmosphere" in result
        assert "gravity" in result

    def test_scan_planet_unknown(self):
        result = json.loads(registry.execute("scan_planet", {"planet_id": "NOPE-99"}))
        assert "error" in result

    def test_check_habitability_returns_score(self):
        result = json.loads(registry.execute(
            "check_habitability",
            {"atmosphere": "nitrogen-oxygen", "gravity": 1.0},
        ))
        assert "habitability_score" in result
        assert result["habitability_score"] > 0

    def test_log_discovery_appends(self):
        MISSION_LOG.clear()
        result = json.loads(registry.execute(
            "log_discovery",
            {"planet_id": "TRAP-1e", "summary": "Breathable atmosphere confirmed."},
        ))
        assert result["status"] == "logged"
        assert len(MISSION_LOG) == 1
        assert MISSION_LOG[0]["planet_id"] == "TRAP-1e"

    def test_scan_planet_schema_auto_generated(self):
        tool = next(t for t in registry.list_tools() if t["function"]["name"] == "scan_planet")
        schema = tool["function"]["parameters"]
        assert schema["properties"]["planet_id"]["type"] == "string"
        assert "planet_id" in schema["required"]

    def test_check_habitability_schema_has_float(self):
        tool = next(t for t in registry.list_tools() if t["function"]["name"] == "check_habitability")
        schema = tool["function"]["parameters"]
        assert schema["properties"]["gravity"]["type"] == "number"
        assert schema["properties"]["atmosphere"]["type"] == "string"
