"""
Exercise 03 — Session Manager
Pluggable session backends: in-memory and file-based.
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
    """Stores sessions in a dict. Fast, but lost on restart."""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    # TODO: implement load, save, exists, list_ids
    pass


class FileBackend:
    """Stores sessions as JSON files in a directory."""

    def __init__(self, directory: Path):
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    # TODO: implement load, save, exists, list_ids
    # Hint: use session_id as filename (sanitise slashes/dots)
    pass


class SessionManager:
    def __init__(self, backend: SessionBackend, system_prompt: str = "You are the DSS Pathfinder ship AI."):
        self.backend = backend
        self.system_prompt = system_prompt

    def get_or_create(self, session_id: str) -> list[dict]:
        """Load existing session or create new one with system prompt."""
        # TODO: implement
        pass

    def append(self, session_id: str, message: dict) -> list[dict]:
        """Add a message to a session and save."""
        # TODO: implement
        pass

    def list_sessions(self) -> list[str]:
        """Return all known session IDs."""
        # TODO: implement
        pass
