"""Tests for Exercise 01 — Memory Store."""

import importlib
import sys
from pathlib import Path


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
    for name in ("start", "solution"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


# --- SessionMemory tests ---

def test_session_add_and_get():
    """SessionMemory.add stores messages and get_messages returns them."""
    mod = _import_start()
    session = mod.SessionMemory(max_turns=10)
    session.add({"role": "user", "content": "hello"})
    session.add({"role": "assistant", "content": "hi"})

    msgs = session.get_messages()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_session_trims_at_max_turns():
    """SessionMemory drops the oldest message when over max_turns."""
    mod = _import_start()
    session = mod.SessionMemory(max_turns=3)

    session.add({"role": "user", "content": "msg1"})
    session.add({"role": "assistant", "content": "msg2"})
    session.add({"role": "user", "content": "msg3"})
    session.add({"role": "assistant", "content": "msg4"})

    msgs = session.get_messages()
    assert len(msgs) == 3
    assert msgs[0]["content"] == "msg2"


def test_session_clear():
    """SessionMemory.clear empties the buffer."""
    mod = _import_start()
    session = mod.SessionMemory()
    session.add({"role": "user", "content": "hello"})
    session.clear()
    assert session.get_messages() == []


# --- LongTermMemory tests ---

def test_remember_and_recall():
    """LongTermMemory stores and recalls entries."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("fav_color", "blue")
    lt.remember("fav_food", "pizza")

    entries = lt.recall()
    assert len(entries) == 2
    keys = [k for k, _ in entries]
    assert "fav_color" in keys
    assert "fav_food" in keys


def test_recall_with_prefix():
    """recall(prefix) filters to matching keys."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("user_name", "Alice")
    lt.remember("user_age", "30")
    lt.remember("project_name", "Phoenix")

    entries = lt.recall(prefix="user")
    assert len(entries) == 2
    keys = [k for k, _ in entries]
    assert all(k.startswith("user") for k in keys)


def test_recall_sorted_by_importance():
    """recall returns entries sorted by importance descending."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("low", "low value", importance=0.3)
    lt.remember("high", "high value", importance=0.9)
    lt.remember("mid", "mid value", importance=0.6)

    entries = lt.recall()
    importances = [e.importance for _, e in entries]
    assert importances == sorted(importances, reverse=True)


def test_forget_marks_entry():
    """forget marks an entry as forgotten and excludes it from recall."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("secret", "hidden")

    assert lt.forget("secret") is True
    assert lt.recall() == []


def test_forget_returns_false_for_missing():
    """forget returns False for non-existent keys."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    assert lt.forget("nonexistent") is False


def test_tick_decay_reduces_importance():
    """tick_decay multiplies importance by factor."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("fact", "something", importance=1.0)
    lt.tick_decay(factor=0.5)

    entries = lt.recall()
    assert len(entries) == 1
    assert abs(entries[0][1].importance - 0.5) < 0.01


def test_tick_decay_removes_weak_entries():
    """tick_decay removes entries that fall below 0.1."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("weak", "fading", importance=0.15)

    removed = lt.tick_decay(factor=0.5)
    assert removed == 1
    assert lt.recall() == []


def test_remember_overwrites():
    """remember with an existing key overwrites the value."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("name", "Alice")
    lt.remember("name", "Bob")

    entries = lt.recall()
    assert len(entries) == 1
    assert entries[0][1].value == "Bob"


# --- build_system_prompt tests ---

def test_build_system_prompt_returns_string():
    """build_system_prompt returns a non-empty string."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    prompt = mod.build_system_prompt(lt)
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_build_system_prompt_includes_memories():
    """build_system_prompt includes stored memories in the output."""
    mod = _import_start()
    lt = mod.LongTermMemory()
    lt.remember("user_name", "Alice")

    prompt = mod.build_system_prompt(lt)
    assert "Alice" in prompt
