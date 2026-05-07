"""
Exercise 01 — Tool Loop
Build the core agent loop: LLM -> tool call -> result -> repeat.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLM(Protocol):
    def chat(self, messages: list[dict]) -> LLMResponse: ...


@dataclass
class LoopResult:
    final_answer: str | None
    tool_calls_made: list[ToolCall]
    steps: int


def run_tool_loop(
    llm: LLM,
    tools: dict[str, Callable[..., str]],
    user_input: str,
    max_steps: int = 10,
) -> LoopResult:
    """
    Run the agent tool loop.

    1. Start with system + user messages.
    2. Call llm.chat(messages).
    3. If response has tool_calls, execute each via `tools[name](**arguments)`,
       append assistant + tool messages, and loop.
    4. If response has content and no tool_calls, return it as final_answer.
    5. Stop after max_steps and return whatever you have.
    """
    # TODO: implement the loop
    pass
