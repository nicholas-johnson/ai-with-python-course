"""
Memory Store — provided from Exercise 01 solution.
SessionMemory, LongTermMemory, and chat utilities.
"""
from __future__ import annotations
import json, time
from dataclasses import dataclass, field
from openai import OpenAI


@dataclass
class MemoryEntry:
    value: str
    importance: float = 1.0
    timestamp: float = field(default_factory=time.time)
    forgotten: bool = False


class SessionMemory:
    """Short-term conversation buffer with a max-turns cap."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[dict] = []

    def add(self, message: dict) -> None:
        self.messages.append(message)
        if len(self.messages) > self.max_turns:
            self.messages.pop(0)

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()


class LongTermMemory:
    """Persistent key-value memory with importance decay and forget."""

    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def remember(self, key: str, value: str, importance: float = 1.0) -> None:
        self._store[key] = MemoryEntry(
            value=value, importance=importance, timestamp=time.time()
        )

    def recall(self, prefix: str = "") -> list[tuple[str, MemoryEntry]]:
        results = []
        for key, entry in self._store.items():
            if entry.forgotten:
                continue
            if prefix and not key.lower().startswith(prefix.lower()):
                continue
            results.append((key, entry))
        results.sort(key=lambda x: x[1].importance, reverse=True)
        return results

    def forget(self, key: str) -> bool:
        if key in self._store:
            self._store[key].forgotten = True
            return True
        return False

    def tick_decay(self, factor: float = 0.9) -> int:
        removed = 0
        to_remove = []
        for key, entry in self._store.items():
            if entry.forgotten:
                continue
            entry.importance *= factor
            if entry.importance < 0.1:
                to_remove.append(key)
        for key in to_remove:
            del self._store[key]
            removed += 1
        return removed


def build_system_prompt(long_term: LongTermMemory) -> str:
    memories = long_term.recall()
    memory_block = ""
    if memories:
        lines = []
        for key, entry in memories[:10]:
            lines.append(f"- {key}: {entry.value} (importance: {entry.importance:.2f})")
        memory_block = (
            "\n\nYou remember the following about your patrons and "
            "past conversations:\n" + "\n".join(lines)
        )

    return (
        "You are BARKEEP, the AI bartender at The Nebula's Edge cantina "
        "on Relay Station Omicron. You remember every patron's drink order, "
        "dietary restrictions, preferences, and stories. You're warm, "
        "slightly wry, and take pride in never forgetting a regular. "
        "When a patron shares something personal, you note it -- a good "
        "bartender always remembers."
        + memory_block
    )


def extract_memories(
    user_msg: str, assistant_msg: str, client: OpenAI
) -> list[dict]:
    """Ask the LLM to identify memorable facts from an exchange."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Analyse this conversation exchange and extract facts worth "
                    "remembering long-term about the user. Return a JSON object with "
                    "a 'memories' array. Each item has 'key' (short label, snake_case) "
                    "and 'value' (the fact). Only include genuinely useful personal facts, "
                    "preferences, or context -- not chitchat. If nothing is worth "
                    "remembering, return {\"memories\": []}."
                ),
            },
            {
                "role": "user",
                "content": f"User said: {user_msg}\nAssistant replied: {assistant_msg}",
            },
        ],
    )
    try:
        data = json.loads(response.choices[0].message.content)
        return data.get("memories", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def chat(
    user_input: str,
    session: SessionMemory,
    long_term: LongTermMemory,
    client: OpenAI,
) -> str:
    session.add({"role": "user", "content": user_input})

    system_prompt = build_system_prompt(long_term)
    messages = [{"role": "system", "content": system_prompt}] + session.get_messages()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    assistant_msg = response.choices[0].message.content
    session.add({"role": "assistant", "content": assistant_msg})

    new_memories = extract_memories(user_input, assistant_msg, client)
    for mem in new_memories:
        key = mem.get("key", "")
        value = mem.get("value", "")
        if key and value:
            long_term.remember(key, value)

    return assistant_msg
