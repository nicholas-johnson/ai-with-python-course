"""
Conversation Summary — provided from Exercise 02 solution.
summarise_turns and SmartSessionMemory.
"""
from __future__ import annotations
from openai import OpenAI

from memory_store import SessionMemory


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
    return response.choices[0].message.content


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

    def add(self, message: dict) -> None:
        super().add(message)

        if len(self.messages) > self.summarise_threshold and self.client:
            half = len(self.messages) // 2
            old_turns = self.messages[:half]

            summary_text = summarise_turns(old_turns, self.client)
            self.summary = (
                self.summary + "\n" + summary_text
                if self.summary
                else summary_text
            )

            summary_msg = {
                "role": "system",
                "content": f"[Summary of earlier conversation] {summary_text}",
            }
            self.messages = [summary_msg] + self.messages[half:]

    def get_summary(self) -> str:
        """Return the accumulated conversation summary."""
        return self.summary
