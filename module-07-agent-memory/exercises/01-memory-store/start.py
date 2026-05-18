"""
Exercise 01 — Memory Store
Build session memory (capped turns) and long-term memory (decay + forget),
then wire them into an interactive chat agent.

Run:  python start.py
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


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
        # TODO: append message and trim oldest if over max_turns
        raise NotImplementedError("TODO")

    def get_messages(self) -> list[dict]:
        # TODO: return current message list
        raise NotImplementedError("TODO")

    def clear(self) -> None:
        self.messages.clear()


class LongTermMemory:
    """Persistent key-value memory with importance decay and forget."""

    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def remember(self, key: str, value: str, importance: float = 1.0) -> None:
        # TODO: store a MemoryEntry (overwrite if exists, refresh timestamp)
        raise NotImplementedError("TODO")

    def recall(self, prefix: str = "") -> list[tuple[str, MemoryEntry]]:
        # TODO: return non-forgotten entries matching prefix (or all if empty),
        #       sorted by importance desc
        raise NotImplementedError("TODO")

    def forget(self, key: str) -> bool:
        # TODO: mark entry as forgotten, return True if found
        raise NotImplementedError("TODO")

    def tick_decay(self, factor: float = 0.9) -> int:
        # TODO: multiply importance by factor for all non-forgotten entries,
        #       return count of entries below 0.1 threshold (remove them)
        raise NotImplementedError("TODO")


def build_system_prompt(long_term: LongTermMemory) -> str:
    # TODO: build a system prompt that includes relevant long-term memories
    #   1. Call long_term.recall() to get active memories
    #   2. Format them into a system prompt string
    #   3. Return the complete prompt
    raise NotImplementedError("TODO")


def chat(
    user_input: str,
    session: SessionMemory,
    long_term: LongTermMemory,
    client: OpenAI,
) -> str:
    # TODO: implement the chat function
    #   1. Add the user message to session memory
    #   2. Build the system prompt with long-term memories
    #   3. Construct messages: [system_prompt] + session.get_messages()
    #   4. Call client.chat.completions.create with model="gpt-4o-mini"
    #   5. Add the assistant response to session memory
    #   6. Auto-detect facts worth remembering (second LLM call)
    #   7. Return the response text
    raise NotImplementedError("TODO")


def main():
    client = OpenAI()
    session = SessionMemory(max_turns=20)
    long_term = LongTermMemory()

    print("=== Agent Memory Chat ===")
    print("Commands: /memories, /decay, /forget <key>, /session, quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/memories":
            entries = long_term.recall()
            if not entries:
                print("[No long-term memories stored]\n")
            else:
                for key, entry in entries:
                    print(
                        f"  {key}: {entry.value} "
                        f"(importance: {entry.importance:.2f})"
                    )
                print()
            continue

        if user_input == "/decay":
            removed = long_term.tick_decay()
            print(f"[Decay applied. {removed} weak memories removed]\n")
            continue

        if user_input.startswith("/forget "):
            key = user_input[8:].strip()
            if long_term.forget(key):
                print(f"[Forgot: {key}]\n")
            else:
                print(f"[No memory found for: {key}]\n")
            continue

        if user_input == "/session":
            msgs = session.get_messages()
            print(
                f"[Session buffer: {len(msgs)} messages "
                f"(max {session.max_turns})]"
            )
            for m in msgs[-6:]:
                print(f"  {m['role']}: {m['content'][:80]}...")
            print()
            continue

        response = chat(user_input, session, long_term, client)
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    main()
