"""
Exercise 01 — Tool Loop (solution)
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
    messages: list[dict] = [
        {"role": "system", "content": "You are the DSS Pathfinder ship AI."},
        {"role": "user", "content": user_input},
    ]
    all_tool_calls: list[ToolCall] = []
    steps = 0

    for _ in range(max_steps):
        steps += 1
        response = llm.chat(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                result = tools[tc.name](**tc.arguments)
                all_tool_calls.append(tc)
                messages.append({
                    "role": "assistant",
                    "tool_calls": [{"id": tc.id, "name": tc.name, "arguments": tc.arguments}],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        elif response.content:
            return LoopResult(
                final_answer=response.content,
                tool_calls_made=all_tool_calls,
                steps=steps,
            )
        else:
            break

    return LoopResult(
        final_answer=None,
        tool_calls_made=all_tool_calls,
        steps=steps,
    )
