"""
Demo: Evaluation harness — golden tests, replay, deterministic mocks.
Run:  python module-02-agent-core/demo/04_eval_harness.py
"""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoldenCase:
    name: str
    user_input: str
    expected_tool_calls: list[dict]
    expected_final_answer: str | None = None


@dataclass
class MockLLMResponse:
    content: str | None = None
    tool_calls: list[dict] = field(default_factory=list)


class MockLLM:
    """Deterministic LLM mock that returns pre-scripted responses."""

    def __init__(self, responses: list[MockLLMResponse]):
        self._responses = list(responses)
        self._call_count = 0

    def chat(self, messages: list[dict]) -> MockLLMResponse:
        if self._call_count >= len(self._responses):
            return MockLLMResponse(content="(no more scripted responses)")
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


def run_agent_loop(llm: MockLLM, user_input: str, tool_handler) -> dict:
    """Minimal agent loop for evaluation."""
    messages = [
        {"role": "system", "content": "You are the Pathfinder ship AI."},
        {"role": "user", "content": user_input},
    ]
    tool_calls_made = []
    final_answer = None

    for _ in range(10):  # max iterations
        response = llm.chat(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                result = tool_handler(tc["name"], tc["arguments"])
                tool_calls_made.append(tc)
                messages.append({"role": "assistant", "tool_calls": [tc]})
                messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result})
        elif response.content:
            final_answer = response.content
            break

    return {"tool_calls": tool_calls_made, "final_answer": final_answer}


def evaluate_golden(case: GoldenCase, result: dict) -> dict:
    """Check result against golden expectations."""
    checks = {}

    actual_tool_names = [tc["name"] for tc in result["tool_calls"]]
    expected_tool_names = [tc["name"] for tc in case.expected_tool_calls]
    checks["tool_names_match"] = actual_tool_names == expected_tool_names

    if case.expected_final_answer:
        checks["answer_contains_expected"] = (
            case.expected_final_answer.lower() in (result["final_answer"] or "").lower()
        )

    checks["passed"] = all(checks.values())
    return checks


if __name__ == "__main__":
    def mock_tool_handler(name: str, arguments: dict) -> str:
        if name == "get_crew_count":
            return json.dumps({"department": arguments.get("department"), "count": 3})
        return json.dumps({"error": "unknown tool"})

    golden = GoldenCase(
        name="crew count query",
        user_input="How many people are in the science department?",
        expected_tool_calls=[{"name": "get_crew_count", "arguments": {"department": "science"}}],
        expected_final_answer="3",
    )

    llm = MockLLM([
        MockLLMResponse(
            tool_calls=[{"id": "call_1", "name": "get_crew_count", "arguments": {"department": "science"}}]
        ),
        MockLLMResponse(content="The science department has 3 crew members."),
    ])

    print("=== Evaluation Harness Demo ===\n")
    print(f"Golden case: {golden.name}")
    print(f"User input:  {golden.user_input}\n")

    result = run_agent_loop(llm, golden.user_input, mock_tool_handler)
    print(f"Tool calls made: {[tc['name'] for tc in result['tool_calls']]}")
    print(f"Final answer:    {result['final_answer']}\n")

    checks = evaluate_golden(golden, result)
    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")
