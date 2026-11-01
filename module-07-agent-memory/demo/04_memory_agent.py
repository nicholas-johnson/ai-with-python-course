"""Part 4: A chat that writes long-term memories as you talk."""

import os
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


class SessionMemory:
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[dict] = []

    def add(self, message: dict) -> None:
        self.messages.append(message)
        while len(self.messages) > self.max_turns:
            self.messages.pop(0)

    def get_messages(self) -> list[dict]:
        return list(self.messages)


@dataclass
class MemoryEntry:
    value: str
    importance: float = 1.0
    timestamp: float = field(default_factory=time.time)
    forgotten: bool = False


class LongTermMemory:
    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def remember(self, key: str, value: str, importance: float = 1.0) -> None:
        self._store[key] = MemoryEntry(value=value, importance=importance)

    def recall(self, prefix: str = "") -> list[tuple[str, MemoryEntry]]:
        results = [
            (key, entry) for key, entry in self._store.items()
            if not entry.forgotten and (not prefix or key.startswith(prefix))
        ]
        return sorted(results, key=lambda item: item[1].importance, reverse=True)


class RememberDecision(BaseModel):
    remember: bool
    key: str | None = Field(description="Short snake_case key, or null if remember is false")
    value: str | None = Field(description="What to remember, or null if remember is false")


def build_system_prompt(long_term: LongTermMemory) -> dict:
    memories = long_term.recall()
    memory_block = ""
    if memories:
        lines = [f"- {key}: {entry.value}" for key, entry in memories[:10]]
        memory_block = (
            "\n\nYou have the following long-term memories about the user:\n"
            + "\n".join(lines)
        )
    return {
        "role": "system",
        "content": (
            "You are a helpful AI assistant on the DSS Pathfinder. "
            "You remember things the user tells you and use that context "
            "in your responses. Be concise and helpful."
            + memory_block
        ),
    }


def _auto_remember(user_input: str, long_term: LongTermMemory, client: OpenAI):
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=RememberDecision,
        input=[
            {
                "role": "system",
                "content": (
                    "Analyse the user message. Decide whether it contains a preference, "
                    "fact, or instruction worth remembering long-term."
                ),
            },
            {"role": "user", "content": user_input},
        ],
    )
    decision = response.output_parsed
    if decision and decision.remember and decision.key and decision.value:
        long_term.remember(decision.key, decision.value)


def chat(user_input: str, session: SessionMemory, long_term: LongTermMemory, client: OpenAI) -> str:
    session.add({"role": "user", "content": user_input})
    messages = [build_system_prompt(long_term)] + session.get_messages()
    response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
    reply = response.output_text
    session.add({"role": "assistant", "content": reply})
    _auto_remember(user_input, long_term, client)
    return reply


def demo_memory_agent(client: OpenAI):
    print("=" * 60)
    print("PART 4: MEMORY-ENHANCED AGENT")
    print("=" * 60)
    print()
    print("  Try telling it your name, preferences, or facts.")
    print("  Then ask it to recall them. Type 'quit' to return.\n")

    session = SessionMemory(max_turns=20)
    long_term = LongTermMemory()

    demo_messages = [
        "My name is Commander Voss and I prefer concise briefings.",
        "What's the reactor status? I like detailed numbers.",
        "Remember that the Kepler mission launches on stardate 2288.1.",
    ]
    for message in demo_messages:
        print(f"  You: {message}")
        print(f"  Agent: {chat(message, session, long_term, client)}\n")

    print("  Long-term memories auto-detected:")
    for key, entry in long_term.recall():
        print(f"    {key}: {entry.value}")
    print("\n  Now try it yourself (type 'quit' to return):\n")

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() == "quit":
            break
        print(f"  Agent: {chat(user_input, session, long_term, client)}\n")

    print("\n  Final long-term memories:")
    for key, entry in long_term.recall():
        print(f"    {key}: {entry.value} (importance: {entry.importance:.2f})")
    print()
