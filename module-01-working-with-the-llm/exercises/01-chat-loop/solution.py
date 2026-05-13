"""
Exercise 01 — Chat Loop (solution)
"""

from dataclasses import dataclass, field
from typing import Protocol


class LLM(Protocol):
    def chat(self, messages: list[dict]) -> str: ...


@dataclass
class ChatBot:
    llm: LLM
    system_prompt: str = "You are the DSS Pathfinder ship AI."
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.messages:
            self.messages = [{"role": "system", "content": self.system_prompt}]

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        response = self.llm.chat(self.messages)
        self.messages.append({"role": "assistant", "content": response})
        return response

    def clear(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def get_history(self) -> list[dict]:
        return self.messages
