"""Tests for Exercise 03 — Session Manager."""

import tempfile
from pathlib import Path

import pytest

from start import FileBackend, InMemoryBackend, SessionManager


class TestInMemoryBackend:
    def test_save_and_load(self):
        backend = InMemoryBackend()
        backend.save("s1", [{"role": "user", "content": "hi"}])
        assert backend.load("s1") == [{"role": "user", "content": "hi"}]

    def test_exists(self):
        backend = InMemoryBackend()
        assert backend.exists("s1") is False
        backend.save("s1", [])
        assert backend.exists("s1") is True

    def test_load_missing(self):
        backend = InMemoryBackend()
        assert backend.load("nope") == []

    def test_list_ids(self):
        backend = InMemoryBackend()
        backend.save("a", [])
        backend.save("b", [])
        assert set(backend.list_ids()) == {"a", "b"}


class TestFileBackend:
    @pytest.fixture()
    def backend(self, tmp_path):
        return FileBackend(tmp_path)

    def test_save_and_load(self, backend):
        backend.save("s1", [{"role": "user", "content": "hello"}])
        loaded = backend.load("s1")
        assert loaded == [{"role": "user", "content": "hello"}]

    def test_exists(self, backend):
        assert backend.exists("s1") is False
        backend.save("s1", [])
        assert backend.exists("s1") is True

    def test_load_missing(self, backend):
        assert backend.load("nope") == []

    def test_list_ids(self, backend):
        backend.save("a", [])
        backend.save("b", [])
        assert set(backend.list_ids()) == {"a", "b"}

    def test_persistence(self, tmp_path):
        b1 = FileBackend(tmp_path)
        b1.save("s1", [{"role": "user", "content": "persisted"}])
        b2 = FileBackend(tmp_path)
        assert b2.load("s1") == [{"role": "user", "content": "persisted"}]


class _SessionManagerTests:
    """Shared tests run against both backends."""

    def make_manager(self):
        raise NotImplementedError

    def test_get_or_create_new(self):
        mgr = self.make_manager()
        msgs = mgr.get_or_create("s1")
        assert len(msgs) == 1
        assert msgs[0]["role"] == "system"

    def test_get_or_create_existing(self):
        mgr = self.make_manager()
        mgr.get_or_create("s1")
        mgr.append("s1", {"role": "user", "content": "hi"})
        msgs = mgr.get_or_create("s1")
        assert len(msgs) == 2

    def test_append(self):
        mgr = self.make_manager()
        mgr.get_or_create("s1")
        msgs = mgr.append("s1", {"role": "user", "content": "test"})
        assert len(msgs) == 2
        assert msgs[-1]["content"] == "test"

    def test_list_sessions(self):
        mgr = self.make_manager()
        mgr.get_or_create("a")
        mgr.get_or_create("b")
        assert set(mgr.list_sessions()) == {"a", "b"}


class TestSessionManagerInMemory(_SessionManagerTests):
    def make_manager(self):
        return SessionManager(InMemoryBackend())

    def test_get_or_create_new(self):
        super().test_get_or_create_new()

    def test_get_or_create_existing(self):
        super().test_get_or_create_existing()

    def test_append(self):
        super().test_append()

    def test_list_sessions(self):
        super().test_list_sessions()


class TestSessionManagerFile(_SessionManagerTests):
    def make_manager(self):
        self._tmpdir = tempfile.mkdtemp()
        return SessionManager(FileBackend(Path(self._tmpdir)))

    def test_get_or_create_new(self):
        super().test_get_or_create_new()

    def test_get_or_create_existing(self):
        super().test_get_or_create_existing()

    def test_append(self):
        super().test_append()

    def test_list_sessions(self):
        super().test_list_sessions()
