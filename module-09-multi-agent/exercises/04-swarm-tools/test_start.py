"""Tests for Exercise 04 — Swarm Agents with Scoped Tools."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock


def _ensure_deps():
    """Stub optional imports so tests run without a full venv."""
    try:
        from dotenv import load_dotenv  # noqa: F401
    except ImportError:
        dotenv = MagicMock()
        dotenv.load_dotenv = lambda *a, **k: None
        sys.modules["dotenv"] = dotenv
    try:
        from openai import OpenAI  # noqa: F401
    except (ImportError, AttributeError):
        mock_openai = MagicMock()
        mock_openai.OpenAI = MagicMock
        sys.modules["openai"] = mock_openai


def _import_start():
    """Import solution.py (or start.py) as a module."""
    _ensure_deps()
    ex_dir = Path(__file__).resolve().parent
    if str(ex_dir) not in sys.path:
        sys.path.insert(0, str(ex_dir))

    for name in ("solution", "start"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            if hasattr(mod, "swarm_loop"):
                return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def _tool_call(tc_id: str, name: str, arguments: str):
    tc = MagicMock()
    tc.id = tc_id
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


def _assistant_message(content=None, tool_calls=None):
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    return msg


def _mock_client_for_message(message):
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=message)]
    mock.chat.completions.create.return_value = mock_response
    return mock


# --- build_agent_messages ---


def test_build_agent_messages_has_system_and_user():
    mod = _import_start()
    messages = mod.build_agent_messages("comms", "Decrypt X42")
    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Communications" in messages[0]["content"] or "comms" in messages[0]["content"].lower()
    assert messages[1]["content"] == "Decrypt X42"


def test_build_agent_messages_engineering_prompt():
    mod = _import_start()
    messages = mod.build_agent_messages("engineering", "Reactor status?")
    assert "Engineer" in messages[0]["content"] or "engineering" in messages[0]["content"].lower()


# --- run_agent_turn ---


def test_run_agent_turn_passes_scoped_tools():
    mod = _import_start()
    client = _mock_client_for_message(_assistant_message(content="Done."))
    messages = mod.build_agent_messages("tactical", "Shields?")
    mod.run_agent_turn("tactical", messages, client)

    call_kwargs = client.chat.completions.create.call_args.kwargs
    tools = call_kwargs.get("tools", [])
    tool_names = {t["function"]["name"] for t in tools}
    assert "check_shields" in tool_names
    assert "scan_threats" in tool_names
    assert "transfer_to_comms" in tool_names
    assert "transfer_to_engineering" in tool_names
    assert "transfer_to_tactical" not in tool_names


def test_run_agent_turn_calls_openai():
    mod = _import_start()
    client = _mock_client_for_message(_assistant_message(content="OK"))
    mod.run_agent_turn("comms", [{"role": "user", "content": "hi"}], client)
    assert client.chat.completions.create.called


# --- handle_tool_calls ---


def test_handle_tool_calls_domain_tool():
    mod = _import_start()
    msg = _assistant_message(
        tool_calls=[_tool_call("tc1", "decrypt_signal", json.dumps({"signal_id": "X42"}))]
    )
    tool_msgs, transfer = mod.handle_tool_calls(msg, "comms")
    assert transfer is None
    assert any(m.get("role") == "tool" for m in tool_msgs)
    tool_content = next(m["content"] for m in tool_msgs if m.get("role") == "tool")
    assert "X42" in tool_content


def test_handle_tool_calls_detects_transfer():
    mod = _import_start()
    msg = _assistant_message(
        tool_calls=[_tool_call("tc1", "transfer_to_engineering", "{}")]
    )
    tool_msgs, transfer = mod.handle_tool_calls(msg, "comms")
    assert transfer == "engineering"


def test_handle_tool_calls_empty_when_no_tools():
    mod = _import_start()
    msg = _assistant_message(content="Final.", tool_calls=None)
    tool_msgs, transfer = mod.handle_tool_calls(msg, "comms")
    assert tool_msgs == []
    assert transfer is None


# --- swarm_loop ---


def test_swarm_loop_final_answer_no_tools():
    mod = _import_start()
    client = _mock_client_for_message(_assistant_message(content="All clear."))
    result = mod.swarm_loop("Status?", client, start_dept="tactical", max_hops=3)
    assert result["answer"] == "All clear."
    assert result["chain"] == ["tactical"]
    assert client.chat.completions.create.call_count == 1


def test_swarm_loop_follows_handoff():
    mod = _import_start()

    calls = []

    def side_effect(**kwargs):
        calls.append(kwargs)
        messages = kwargs.get("messages", [])
        # First turn: comms with transfer
        if len(calls) == 1:
            return MagicMock(
                choices=[
                    MagicMock(
                        message=_assistant_message(
                            tool_calls=[
                                _tool_call("tc1", "transfer_to_engineering", "{}")
                            ]
                        )
                    )
                ]
            )
        # Second turn: engineering final answer
        return MagicMock(
            choices=[MagicMock(message=_assistant_message(content="Reactor is fine."))]
        )

    client = MagicMock()
    client.chat.completions.create.side_effect = side_effect

    result = mod.swarm_loop(
        "Check reactor after decrypting X42",
        client,
        start_dept="comms",
        max_hops=5,
    )
    assert "engineering" in result["chain"]
    assert result["answer"] == "Reactor is fine."
    assert client.chat.completions.create.call_count >= 2


def test_swarm_loop_respects_max_hops():
    mod = _import_start()

    def always_tools(**kwargs):
        return MagicMock(
            choices=[
                MagicMock(
                    message=_assistant_message(
                        tool_calls=[_tool_call("tc1", "scan_frequencies", "{}")]
                    )
                )
            ]
        )

    client = MagicMock()
    client.chat.completions.create.side_effect = always_tools

    result = mod.swarm_loop("loop forever", client, start_dept="comms", max_hops=2)
    assert "max hops" in result["answer"].lower()
    assert client.chat.completions.create.call_count <= 2


def test_swarm_loop_returns_trace_and_chain():
    mod = _import_start()
    client = _mock_client_for_message(_assistant_message(content="Done."))
    result = mod.swarm_loop("Hi", client, start_dept="comms", max_hops=4)
    assert "trace" in result
    assert "chain" in result
    assert isinstance(result["trace"], list)
