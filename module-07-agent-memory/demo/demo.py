"""
Module 7 — Agent Memory Demo

Interactive walkthrough of memory patterns for AI agents.
Covers session memory, long-term memory with decay, summarisation,
and a memory-enhanced chatbot.

Run:  python module-07-agent-memory/demo/demo.py
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ---------------------------------------------------------------------------
# Part 1 — Session Memory
# ---------------------------------------------------------------------------

class SessionMemory:
    """Capped message buffer — oldest messages are evicted first."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[dict] = []

    def add(self, message: dict) -> None:
        self.messages.append(message)
        while len(self.messages) > self.max_turns:
            self.messages.pop(0)

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()


# ---------------------------------------------------------------------------
# Part 2 — Long-Term Memory
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    value: str
    importance: float = 1.0
    timestamp: float = field(default_factory=time.time)
    forgotten: bool = False


class LongTermMemory:
    """Key-value store with importance decay and explicit forget."""

    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def remember(self, key: str, value: str, importance: float = 1.0) -> None:
        self._store[key] = MemoryEntry(value=value, importance=importance)

    def recall(self, prefix: str = "") -> list[tuple[str, MemoryEntry]]:
        results = [
            (k, v) for k, v in self._store.items()
            if not v.forgotten and (not prefix or k.startswith(prefix))
        ]
        return sorted(results, key=lambda x: x[1].importance, reverse=True)

    def forget(self, key: str) -> bool:
        if key in self._store:
            self._store[key].forgotten = True
            return True
        return False

    def tick_decay(self, factor: float = 0.9) -> int:
        removed = 0
        to_delete = []
        for key, entry in self._store.items():
            if not entry.forgotten:
                entry.importance *= factor
                if entry.importance < 0.1:
                    to_delete.append(key)
        for key in to_delete:
            del self._store[key]
            removed += 1
        return removed


# ---------------------------------------------------------------------------
# Part 3 — Summarisation
# ---------------------------------------------------------------------------

def summarise_turns(turns: list[dict], client: OpenAI) -> str:
    """Ask the LLM to compress a conversation into a short summary."""
    formatted = "\n".join(f"{t['role']}: {t['content']}" for t in turns)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarise the following conversation in 2-3 sentences. "
                    "Preserve key facts, decisions, and any action items."
                ),
            },
            {"role": "user", "content": formatted},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Part 4 — Memory-Enhanced Agent
# ---------------------------------------------------------------------------

def build_system_prompt(long_term: LongTermMemory) -> dict:
    memories = long_term.recall()
    memory_block = ""
    if memories:
        lines = [f"- {k}: {e.value}" for k, e in memories[:10]]
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


def chat(
    user_input: str,
    session: SessionMemory,
    long_term: LongTermMemory,
    client: OpenAI,
) -> str:
    session.add({"role": "user", "content": user_input})
    system = build_system_prompt(long_term)
    messages = [system] + session.get_messages()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    reply = response.choices[0].message.content
    session.add({"role": "assistant", "content": reply})

    _auto_remember(user_input, long_term, client)
    return reply


def _auto_remember(user_input: str, long_term: LongTermMemory, client: OpenAI):
    """Ask the LLM if the user said anything worth remembering."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Analyse the user message. If it contains a preference, fact, or "
                    "instruction worth remembering long-term, return JSON: "
                    '{"remember": true, "key": "short_key", "value": "what to remember"}. '
                    'Otherwise return {"remember": false}.'
                ),
            },
            {"role": "user", "content": user_input},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    if data.get("remember"):
        long_term.remember(data["key"], data["value"])


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

def wait():
    input("\n--- Press Enter to continue ---\n")


def main():
    client = OpenAI()

    print("=" * 60)
    print("  MODULE 7 DEMO — Agent Memory")
    print("=" * 60)

    # ---- Part 1: Session Memory ----
    print("\n## Part 1: Session Memory\n")
    print("Session memory is a capped buffer of recent messages.")
    print("When it fills up, the oldest messages are evicted.\n")

    session = SessionMemory(max_turns=4)
    messages = [
        {"role": "user", "content": "What's the reactor status?"},
        {"role": "assistant", "content": "Reactor is at 98% efficiency."},
        {"role": "user", "content": "Any anomalies?"},
        {"role": "assistant", "content": "No anomalies detected."},
        {"role": "user", "content": "Check the navigation array."},
    ]

    for msg in messages:
        session.add(msg)
        print(f"  Added: {msg['role']}: {msg['content'][:60]}")
        print(f"  Buffer size: {len(session.get_messages())} / {session.max_turns}")

    print(f"\n  Final buffer ({len(session.get_messages())} messages):")
    for m in session.get_messages():
        print(f"    {m['role']}: {m['content']}")

    wait()

    # ---- Part 2: Long-Term Memory ----
    print("## Part 2: Long-Term Memory\n")
    print("Long-term memory persists across sessions.")
    print("Entries have importance scores that decay over time.\n")

    ltm = LongTermMemory()
    ltm.remember("user_name", "Commander Voss", importance=1.0)
    ltm.remember("briefing_style", "Prefers concise bullet points", importance=0.8)
    ltm.remember("reactor_history", "Ion storm caused 15% drop last month", importance=0.6)

    print("  Stored 3 memories:")
    for key, entry in ltm.recall():
        print(f"    {key}: {entry.value} (importance: {entry.importance:.2f})")

    print("\n  Applying decay (factor=0.7) three times...")
    for i in range(3):
        removed = ltm.tick_decay(factor=0.7)
        remaining = ltm.recall()
        print(f"    Round {i+1}: {removed} removed, {len(remaining)} remaining")
        for key, entry in remaining:
            print(f"      {key}: importance={entry.importance:.3f}")

    print("\n  Forgetting 'user_name'...")
    ltm.forget("user_name")
    print(f"  Recall 'user_name': {[k for k, _ in ltm.recall('user_name')]}")

    wait()

    # ---- Part 3: Summarisation ----
    print("## Part 3: Summarisation\n")
    print("When conversations get long, we summarise old turns")
    print("to save tokens while preserving key information.\n")

    conversation = [
        {"role": "user", "content": "I need a full status report on all ship systems."},
        {"role": "assistant", "content": "Reactor: 98% efficiency. Navigation: Online, course locked to Kepler-442b. Life support: Nominal. Shields: 85% charge."},
        {"role": "user", "content": "Why are shields below 100%?"},
        {"role": "assistant", "content": "The ion storm on stardate 2287.3 depleted shield reserves. Recharge rate is 2% per hour — full charge expected in 7.5 hours."},
        {"role": "user", "content": "Prioritise shield recharge. Divert auxiliary power."},
        {"role": "assistant", "content": "Acknowledged. Diverting auxiliary power to shields. New recharge rate: 5% per hour. Full charge in 3 hours."},
        {"role": "user", "content": "What about the sensor array maintenance scheduled for tomorrow?"},
        {"role": "assistant", "content": "Sensor array maintenance is scheduled for 0800 tomorrow. It requires 2 hours downtime. Recommend completing before shield recharge finishes."},
    ]

    print(f"  Original conversation: {len(conversation)} messages")
    total_chars = sum(len(m['content']) for m in conversation)
    print(f"  Total characters: {total_chars}\n")

    print("  Summarising with OpenAI...\n")
    summary = summarise_turns(conversation, client)
    print(f"  Summary ({len(summary)} chars):")
    print(f"  {summary}")
    print(f"\n  Compression ratio: {len(summary)}/{total_chars} = {len(summary)/total_chars:.0%}")

    wait()

    # ---- Part 4: Memory-Enhanced Agent ----
    print("## Part 4: Memory-Enhanced Agent\n")
    print("Now let's chat with an agent that remembers things.\n")
    print("Try telling it your name, preferences, or facts.")
    print("Then ask it to recall them. Type 'quit' to end.\n")

    session = SessionMemory(max_turns=20)
    long_term = LongTermMemory()

    demo_messages = [
        "My name is Commander Voss and I prefer concise briefings.",
        "What's the reactor status? I like detailed numbers.",
        "Remember that the Kepler mission launches on stardate 2288.1.",
    ]

    for msg in demo_messages:
        print(f"  You: {msg}")
        reply = chat(msg, session, long_term, client)
        print(f"  Agent: {reply}\n")

    print("  Long-term memories auto-detected:")
    for key, entry in long_term.recall():
        print(f"    {key}: {entry.value}")

    print("\n  Now try it yourself (type 'quit' to end):\n")
    while True:
        user_input = input("  You: ").strip()
        if not user_input or user_input.lower() == "quit":
            break
        reply = chat(user_input, session, long_term, client)
        print(f"  Agent: {reply}\n")

    print("\n  Final long-term memories:")
    for key, entry in long_term.recall():
        print(f"    {key}: {entry.value} (importance: {entry.importance:.2f})")

    print("\n✓ Demo complete.")


if __name__ == "__main__":
    main()
