"""Tests for Exercise 02 — Tool Agent."""

import os

import pytest
import start


def test_tools_defined():
    """The three ship tools should be LangChain tools with docstring descriptions."""
    if not hasattr(start, "tools"):
        pytest.skip("tools list not defined yet")
    names = {t.name for t in start.tools}
    assert {"classify", "read_sensor", "query_crew"} <= names
    assert all(t.description for t in start.tools)


def test_read_sensor_tool_returns_json():
    if not hasattr(start, "read_sensor"):
        pytest.skip("read_sensor tool not defined yet")
    result = start.read_sensor.invoke({"sensor_name": "docking_seal_integrity"})
    assert '"value"' in result


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_run_agent_returns_string():
    result = start.run_agent("What is the current docking seal integrity?")
    assert isinstance(result, str)
    assert "94" in result
