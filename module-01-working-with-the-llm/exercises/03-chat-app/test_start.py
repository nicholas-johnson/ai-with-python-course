"""Tests for Exercise 03 — Chat App."""

import json
from pathlib import Path

import pytest

from start import SYSTEM_PROMPT, handle_command, load_session, save_session


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------

class TestSaveSession:
    def test_writes_json_file(self, tmp_path):
        filepath = tmp_path / "test.json"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "hello"},
        ]
        save_session(filepath, messages)

        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert len(data) == 2
        assert data[0]["role"] == "system"
        assert data[1]["content"] == "hello"

    def test_overwrites_existing_file(self, tmp_path):
        filepath = tmp_path / "test.json"
        save_session(filepath, [{"role": "system", "content": "v1"}])
        save_session(filepath, [{"role": "system", "content": "v2"}])

        data = json.loads(filepath.read_text())
        assert data[0]["content"] == "v2"


class TestLoadSession:
    def test_loads_existing_file(self, tmp_path):
        filepath = tmp_path / "test.json"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        filepath.write_text(json.dumps(messages))

        loaded = load_session(filepath)
        assert len(loaded) == 3
        assert loaded[1]["content"] == "hello"

    def test_returns_fresh_session_if_missing(self, tmp_path):
        filepath = tmp_path / "nonexistent.json"
        loaded = load_session(filepath)

        assert len(loaded) == 1
        assert loaded[0]["role"] == "system"
        assert loaded[0]["content"] == SYSTEM_PROMPT

    def test_roundtrip(self, tmp_path):
        filepath = tmp_path / "test.json"
        original = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"},
        ]
        save_session(filepath, original)
        loaded = load_session(filepath)

        assert loaded == original


# ---------------------------------------------------------------------------
# Command handler tests
# ---------------------------------------------------------------------------

class TestHandleCommand:
    def _messages(self):
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

    def test_clear_resets_to_system_prompt(self, tmp_path):
        messages = self._messages()
        result = handle_command("/clear", messages, tmp_path / "f.json")

        assert result is not None
        assert len(result) == 1
        assert result[0]["role"] == "system"

    def test_history_returns_messages_unchanged(self, tmp_path, capsys):
        messages = self._messages()
        result = handle_command("/history", messages, tmp_path / "f.json")

        assert result == messages
        captured = capsys.readouterr()
        assert "user" in captured.out
        assert "hello" in captured.out

    def test_save_writes_file(self, tmp_path):
        filepath = tmp_path / "save_test.json"
        messages = self._messages()
        result = handle_command("/save", messages, filepath)

        assert result == messages
        assert filepath.exists()
        data = json.loads(filepath.read_text())
        assert len(data) == 3

    def test_load_reads_file(self, tmp_path):
        filepath = tmp_path / "load_test.json"
        save_session(filepath, self._messages())

        result = handle_command("/load", [{"role": "system", "content": SYSTEM_PROMPT}], filepath)

        assert result is not None
        assert len(result) == 3

    def test_help_returns_messages(self, tmp_path, capsys):
        messages = self._messages()
        result = handle_command("/help", messages, tmp_path / "f.json")

        assert result == messages
        captured = capsys.readouterr()
        assert "/clear" in captured.out
        assert "/save" in captured.out

    def test_unknown_command_returns_none(self, tmp_path):
        messages = self._messages()
        result = handle_command("/unknown", messages, tmp_path / "f.json")

        assert result is None

    def test_clear_then_save_roundtrip(self, tmp_path):
        filepath = tmp_path / "rt.json"
        messages = self._messages()

        messages = handle_command("/clear", messages, filepath)
        assert len(messages) == 1

        handle_command("/save", messages, filepath)
        loaded = handle_command("/load", [], filepath)
        assert len(loaded) == 1
        assert loaded[0]["role"] == "system"
