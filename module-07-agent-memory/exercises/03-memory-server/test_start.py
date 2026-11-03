"""Tests for Exercise 03 — Memory MCP Server."""

import asyncio
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

MEMORY_TOOLS = {"remember", "recall", "forget", "list_memories"}
COMPACTION_TOOLS = {"append_turn", "thread_budget", "compact_thread", "get_anchors"}


def _import_module(name: str):
    """Import a module from the exercise directory."""
    ex_dir = Path(__file__).resolve().parent
    mod_path = ex_dir / f"{name}.py"
    if not mod_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_server():
    """Import server.py (or solution_server.py as fallback)."""
    for name in ("server", "solution_server"):
        mod = _import_module(name)
        if mod and hasattr(mod, "mcp"):
            return mod
    raise FileNotFoundError("Neither server.py nor solution_server.py found with mcp")


def _import_client():
    """Import start.py (or solution.py as fallback)."""
    for name in ("start", "solution"):
        mod = _import_module(name)
        if mod:
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _tools():
    return {tool.name: tool for tool in asyncio.run(_import_server().mcp.list_tools())}


def _fake_tool(name: str, description: str = "Does a thing"):
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.input_schema = {
        "type": "object",
        "properties": {"patron": {"type": "string"}, "text": {"type": "string"}},
        "required": ["patron", "text"],
    }
    return tool


def _tool_result(text: str):
    result = MagicMock()
    content = MagicMock()
    content.text = text
    result.content = [content]
    return result


# ---- the server ----


def test_server_registers_the_memory_tools():
    """remember, recall, forget, and list_memories should all be exposed."""
    missing = MEMORY_TOOLS - set(_tools())
    assert not missing, f"Missing memory tools: {missing}"


def test_server_registers_the_compaction_tools():
    """Compaction is a service too: the thread lives on the server."""
    missing = COMPACTION_TOOLS - set(_tools())
    assert not missing, f"Missing compaction tools: {missing}"


def test_every_tool_has_a_description():
    """The docstring is what tells the model when to call a tool."""
    for name, tool in _tools().items():
        assert tool.description and tool.description.strip(), f"{name} has no description"


def test_remember_takes_a_patron():
    """Memories are namespaced per patron, so the tool has to ask for one."""
    schema = _tools()["remember"].input_schema
    assert "patron" in schema["properties"], f"remember params: {schema['properties']}"


def test_compact_thread_takes_a_thread_id_and_a_budget():
    """Compaction is budget-triggered, per thread."""
    properties = _tools()["compact_thread"].input_schema["properties"]
    assert "thread_id" in properties
    assert "budget_tokens" in properties


# ---- the client ----


def test_mcp_to_openai_tools_converts_one_tool():
    """MCP tool definitions become OpenAI function tools."""
    converted = _import_client().mcp_to_openai_tools([_fake_tool("remember")])

    assert len(converted) == 1
    assert converted[0]["type"] == "function"
    assert converted[0]["name"] == "remember"
    assert converted[0]["description"] == "Does a thing"
    assert converted[0]["parameters"]["required"] == ["patron", "text"]


def test_mcp_to_openai_tools_converts_the_whole_list():
    """All the server's tools should reach the model, in order."""
    tools = [_fake_tool(name) for name in ("remember", "recall", "compact_thread")]
    converted = _import_client().mcp_to_openai_tools(tools)

    assert [tool["name"] for tool in converted] == ["remember", "recall", "compact_thread"]


def test_call_text_returns_the_tool_text():
    client_mod = _import_client()
    session = MagicMock()
    session.call_tool = AsyncMock(return_value=_tool_result("Remembered: extra fizz"))

    text = asyncio.run(client_mod.call_text(session, "remember", {"patron": "zara"}))

    assert text == "Remembered: extra fizz"
    session.call_tool.assert_awaited_once_with("remember", {"patron": "zara"})


def test_call_text_survives_an_empty_result():
    """An empty result should not crash the turn."""
    client_mod = _import_client()
    session = MagicMock()
    empty = MagicMock()
    empty.content = []
    session.call_tool = AsyncMock(return_value=empty)

    assert asyncio.run(client_mod.call_text(session, "forget", {})) == "No result"


def test_run_turn_returns_the_answer_when_no_tools_are_called():
    client_mod = _import_client()
    response = MagicMock()
    response.output = []
    response.output_text = "Comet Tail, extra fizz. Coming up."

    client = MagicMock()
    client.responses.create.return_value = response
    messages = [{"role": "user", "content": "the usual"}]

    answer = asyncio.run(client_mod.run_turn(client, messages, MagicMock(), []))

    assert answer == "Comet Tail, extra fizz. Coming up."
    assert messages[-1] == {"role": "assistant", "content": answer}


def test_run_turn_feeds_the_tool_result_back_to_the_model():
    """A tool call has to come back as function_call_output, keyed by call_id."""
    client_mod = _import_client()

    call = MagicMock()
    call.type = "function_call"
    call.name = "recall"
    call.call_id = "call_1"
    call.arguments = json.dumps({"patron": "zara", "query": "usual drink"})

    first = MagicMock()
    first.output = [call]
    second = MagicMock()
    second.output = []
    second.output_text = "Your usual, then."

    client = MagicMock()
    client.responses.create.side_effect = [first, second]

    session = MagicMock()
    session.call_tool = AsyncMock(return_value=_tool_result("- [preference] Comet Tail"))

    messages = [{"role": "user", "content": "what do I drink?"}]
    answer = asyncio.run(client_mod.run_turn(client, messages, session, []))

    assert answer == "Your usual, then."
    outputs = [m for m in messages if isinstance(m, dict) and m.get("type") == "function_call_output"]
    assert len(outputs) == 1
    assert outputs[0]["call_id"] == "call_1"
    assert "Comet Tail" in outputs[0]["output"]
    assert client.responses.create.call_count == 2


def test_run_turn_gives_up_rather_than_looping_forever():
    """A model that only ever calls tools must still return."""
    client_mod = _import_client()

    call = MagicMock()
    call.type = "function_call"
    call.name = "recall"
    call.call_id = "call_1"
    call.arguments = "{}"
    response = MagicMock()
    response.output = [call]

    client = MagicMock()
    client.responses.create.return_value = response
    session = MagicMock()
    session.call_tool = AsyncMock(return_value=_tool_result("nothing"))

    answer = asyncio.run(client_mod.run_turn(client, [], session, [], max_steps=3))

    assert isinstance(answer, str)
    assert client.responses.create.call_count == 3


def test_record_and_compact_leaves_a_thread_within_budget_alone(monkeypatch):
    """Compaction is triggered by the budget, not by every turn."""
    client_mod = _import_client()
    calls = []

    async def fake_call_text(session, name, arguments):
        calls.append(name)
        return "Thread tonight: 120 tokens in 4 messages — within budget"

    monkeypatch.setattr(client_mod, "call_text", fake_call_text)
    asyncio.run(client_mod.record_and_compact(MagicMock(), "user", "evening"))

    assert calls == ["append_turn", "thread_budget"]


def test_record_and_compact_compacts_when_over_budget(monkeypatch):
    client_mod = _import_client()
    calls = []

    async def fake_call_text(session, name, arguments):
        calls.append(name)
        if name == "thread_budget":
            return "Thread tonight: 900 tokens in 20 messages — over budget"
        return "Compacted 14 messages, 900 -> 300 tokens.\n[earlier conversation]"

    monkeypatch.setattr(client_mod, "call_text", fake_call_text)
    asyncio.run(client_mod.record_and_compact(MagicMock(), "assistant", "on its way"))

    assert calls == ["append_turn", "thread_budget", "compact_thread"]


def test_client_has_main():
    assert hasattr(_import_client(), "main"), "Client module must have a main() function"
