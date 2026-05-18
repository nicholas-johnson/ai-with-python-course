"""
Exercise 02 — Conversation Summary (solution)
Extend the memory store with automatic conversation summarisation.

Run:  python solution.py
"""
from __future__ import annotations
from dotenv import load_dotenv
from openai import OpenAI

from memory_store import (
    SessionMemory,
    LongTermMemory,
    build_system_prompt,
    chat,
)

load_dotenv()


def summarise_turns(turns: list[dict], client: OpenAI) -> str:
    """Summarise a list of conversation turns into a concise paragraph."""
    transcript = "\n".join(
        f"{t['role'].upper()}: {t['content']}" for t in turns
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarise the following conversation into a concise paragraph. "
                    "Preserve key facts, user preferences, decisions made, and any "
                    "important context. Do not include greetings or filler. "
                    "Write in third person past tense."
                ),
            },
            {"role": "user", "content": transcript},
        ],
    )
    return response.choices[0].message.content or ""


class SmartSessionMemory(SessionMemory):
    """Session memory that auto-summarises when the buffer gets too long."""

    def __init__(
        self,
        max_turns: int = 20,
        summarise_threshold: int = 10,
        client: OpenAI | None = None,
    ):
        super().__init__(max_turns=max_turns)
        self.summarise_threshold = summarise_threshold
        self.client = client
        self.summary: str = ""

    def _compress_oldest(self, n: int | None = None) -> str:
        """Summarise the oldest n messages and replace them with a summary message."""
        n = n or len(self.messages) // 2
        old_turns = self.messages[:n]
        summary_text = summarise_turns(old_turns, self.client)
        self.summary = (
            self.summary + "\n" + summary_text if self.summary else summary_text
        )
        self.messages = [
            {"role": "system", "content": f"[Summary of earlier conversation] {summary_text}"}
        ] + self.messages[n:]
        return summary_text

    def add(self, message: dict) -> None:
        super().add(message)
        if len(self.messages) > self.summarise_threshold and self.client:
            n = len(self.messages) // 2
            self._compress_oldest(n)
            print(f"  [Auto-summarised {n} older messages]")

    def get_summary(self) -> str:
        """Return the accumulated conversation summary."""
        return self.summary


def main():
    client = OpenAI()
    session = SmartSessionMemory(
        max_turns=30, summarise_threshold=10, client=client
    )
    long_term = LongTermMemory()

    print("=== The Nebula's Edge — BARKEEP (Smart Memory) ===")
    print("Commands: /summary, /turns, /force-summarise, /memories, quit\n")

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

        if user_input == "/summary":
            s = session.get_summary()
            if s:
                print(f"[Conversation summary]\n{s}\n")
            else:
                print("[No summary yet -- keep chatting!]\n")
            continue

        if user_input == "/turns":
            msgs = session.get_messages()
            print(
                f"[Session buffer: {len(msgs)} messages "
                f"(threshold: {session.summarise_threshold})]\n"
            )
            continue

        if user_input == "/force-summarise":
            if len(session.messages) < 2:
                print("[Not enough messages to summarise]\n")
                continue
            n = len(session.messages) // 2
            session._compress_oldest(n)
            print(f"[Summarised {n} messages]\n")
            continue

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

        response = chat(user_input, session, long_term, client)
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    main()
