"""
Exercise 01 — Chat Loop
Build a conversational chatbot with history management.
"""

from dataclasses import dataclass, field
from typing import Protocol


class LLM(Protocol):
    def chat(self, messages: list[dict]) -> str: ...


@dataclass
class ChatBot:
    """
    A simple chatbot that maintains conversation history.
    """

    llm: LLM
    system_prompt: str = "You are the DSS Pathfinder ship AI."
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.messages:
            self.messages = [{"role": "system", "content": self.system_prompt}]

    def chat(self, user_input: str) -> str:
        """
        1. Append user message to history.
        2. Call self.llm.chat(self.messages) to get a response string.
        3. Append assistant message to history.
        4. Return the response text.
        """
        # TODO: implement
        pass

    def clear(self) -> None:
        """Reset history to just the system prompt."""
        # TODO: implement
        pass

    def get_history(self) -> list[dict]:
        """Return the full message history."""
        # TODO: implement
        pass
