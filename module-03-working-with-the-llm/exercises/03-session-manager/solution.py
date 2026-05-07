"""
Exercise 03 — Session Manager (solution)
"""

import json
from pathlib import Path
from typing import Protocol


class SessionBackend(Protocol):
    def load(self, session_id: str) -> list[dict]: ...
    def save(self, session_id: str, messages: list[dict]) -> None: ...
    def exists(self, session_id: str) -> bool: ...
    def list_ids(self) -> list[str]: ...


class InMemoryBackend:
    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def load(self, session_id: str) -> list[dict]:
        return self._store.get(session_id, [])

    def save(self, session_id: str, messages: list[dict]) -> None:
        self._store[session_id] = messages

    def exists(self, session_id: str) -> bool:
        return session_id in self._store

    def list_ids(self) -> list[str]:
        return list(self._store.keys())


class FileBackend:
    def __init__(self, directory: Path):
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        safe_id = session_id.replace("/", "_").replace("..", "_")
        return self._dir / f"{safe_id}.json"

    def load(self, session_id: str) -> list[dict]:
        path = self._path(session_id)
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def save(self, session_id: str, messages: list[dict]) -> None:
        self._path(session_id).write_text(json.dumps(messages, indent=2))

    def exists(self, session_id: str) -> bool:
        return self._path(session_id).exists()

    def list_ids(self) -> list[str]:
        return [p.stem for p in self._dir.glob("*.json")]


class SessionManager:
    def __init__(self, backend: SessionBackend, system_prompt: str = "You are the DSS Pathfinder ship AI."):
        self.backend = backend
        self.system_prompt = system_prompt

    def get_or_create(self, session_id: str) -> list[dict]:
        if self.backend.exists(session_id):
            return self.backend.load(session_id)
        messages = [{"role": "system", "content": self.system_prompt}]
        self.backend.save(session_id, messages)
        return messages

    def append(self, session_id: str, message: dict) -> list[dict]:
        messages = self.get_or_create(session_id)
        messages.append(message)
        self.backend.save(session_id, messages)
        return messages

    def list_sessions(self) -> list[str]:
        return self.backend.list_ids()
