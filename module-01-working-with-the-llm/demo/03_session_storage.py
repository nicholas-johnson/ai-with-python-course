"""
Demo: Session storage — in-memory, file-based, and the pluggable pattern.
Run:  python module-01-working-with-the-llm/demo/03_session_storage.py
"""

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class SessionBackend(Protocol):
    """Pluggable session storage interface."""

    def load(self, session_id: str) -> list[dict]: ...
    def save(self, session_id: str, messages: list[dict]) -> None: ...
    def exists(self, session_id: str) -> bool: ...


class InMemoryBackend:
    """Stores sessions in a plain dict — fast but lost on restart."""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def load(self, session_id: str) -> list[dict]:
        return self._store.get(session_id, [])

    def save(self, session_id: str, messages: list[dict]) -> None:
        self._store[session_id] = messages

    def exists(self, session_id: str) -> bool:
        return session_id in self._store


class FileBackend:
    """Stores sessions as JSON files — survives restarts."""

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


@dataclass
class SessionManager:
    """Manages chat sessions using a pluggable backend."""

    backend: SessionBackend
    system_prompt: str = "You are the DSS Pathfinder ship AI."

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


if __name__ == "__main__":
    print("=== Session Storage Demo ===\n")

    print("1. In-memory backend:")
    mem_manager = SessionManager(backend=InMemoryBackend())
    msgs = mem_manager.get_or_create("session-1")
    print(f"   New session: {len(msgs)} messages")
    mem_manager.append("session-1", {"role": "user", "content": "Ship status?"})
    mem_manager.append("session-1", {"role": "assistant", "content": "All systems nominal."})
    msgs = mem_manager.get_or_create("session-1")
    print(f"   After chat: {len(msgs)} messages")

    print("\n2. File backend:")
    with tempfile.TemporaryDirectory() as tmpdir:
        file_manager = SessionManager(backend=FileBackend(Path(tmpdir)))
        file_manager.get_or_create("session-2")
        file_manager.append("session-2", {"role": "user", "content": "Crew count?"})
        file_manager.append("session-2", {"role": "assistant", "content": "12 active crew."})

        reloaded = FileBackend(Path(tmpdir))
        msgs = reloaded.load("session-2")
        print(f"   Reloaded from disk: {len(msgs)} messages")
        print(f"   Last message: {msgs[-1]['content']}")

    print("\n3. Pluggable pattern:")
    print("   SessionManager works with any backend that implements load/save/exists.")
    print("   Swap InMemoryBackend for FileBackend, Redis, Postgres — same interface.")
