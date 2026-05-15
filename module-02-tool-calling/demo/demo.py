"""
Module 2 Demo — Tool Calling
Run:  python module-02-tool-calling/demo/demo.py

Walks through the full module in one script:
  Part 1: Message format — make a real tool call, trace the 4 message roles
  Part 2: Tool registry — decorator registration, validation, routing, error handling
  Part 3: Safety rails — allowlists, rate limits, redaction, audit logs
  Part 4: Eval harness — golden tests with a mock LLM (no API calls)

Requires: OPENAI_API_KEY environment variable (Parts 1 only).
"""

import json
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from openai import OpenAI

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")


# ---------------------------------------------------------------------------
# Part 1: Message format — live tool call
# ---------------------------------------------------------------------------


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_crew",
            "description": "Query crew members assigned to a mission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "active_mission": {
                        "type": "string",
                        "description": "Mission ID",
                    },
                },
                "required": ["active_mission"],
            },
        },
    },
]

CREW_DB = {
    "MSN-001": [
        {"id": "CRW-001", "name": "Commander Elara Voss"},
        {"id": "CRW-003", "name": "Chief Engineer Mira Chen"},
        {"id": "CRW-005", "name": "Ensign Dax Morel"},
        {"id": "CRW-011", "name": "Specialist Bodhi Kwan"},
    ],
}


def execute_tool(name: str, arguments: dict) -> str:
    if name == "query_crew":
        crew = CREW_DB.get(arguments.get("active_mission", ""), [])
        return json.dumps(crew)
    return json.dumps({"error": f"Unknown tool: {name}"})


def demo_message_format(client: OpenAI):
    section("Part 1: Message Format — Live Tool Call")

    print("  Sending a question that will trigger a tool call...")
    print("  Question: 'Who is assigned to mission MSN-001?'\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. You have access to a query_crew tool "
                "for looking up crew assigned to missions. Always cite the data source."
            ),
        },
        {"role": "user", "content": "Who is assigned to mission MSN-001?"},
    ]

    print("  [SYSTEM] Sets the agent persona + available tools")
    print("  [USER]   'Who is assigned to mission MSN-001?'")

    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS
    )
    assistant_msg = response.choices[0].message

    if assistant_msg.tool_calls:
        tc = assistant_msg.tool_calls[0]
        print(f"  [ASSISTANT] tool_call: {tc.function.name}({tc.function.arguments})")

        args = json.loads(tc.function.arguments)
        result = execute_tool(tc.function.name, args)
        print(f"  [TOOL]      result: {result[:80]}...")

        messages.append(assistant_msg)
        messages.append(
            {"role": "tool", "tool_call_id": tc.id, "content": result}
        )

        final = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        print(f"  [ASSISTANT] {final.choices[0].message.content}")
    else:
        print(f"  [ASSISTANT] {assistant_msg.content}")

    print("\n  Key points:")
    print("  • 4 roles: system, user, assistant, tool")
    print("  • Assistant decides whether to call a tool or answer directly")
    print("  • Tool results feed back as messages — the model interprets them")
    print("  • This loop is the foundation of every agent")


# ---------------------------------------------------------------------------
# Part 2: Tool registry — decorator pattern
# ---------------------------------------------------------------------------


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSchema] = {}

    def register(self, name: str, description: str, parameters: dict):
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = ToolSchema(
                name=name, description=description, parameters=parameters, handler=fn
            )
            return fn
        return decorator

    def list_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})
        tool = self._tools[name]
        try:
            result = tool.handler(**arguments)
            return json.dumps(result) if not isinstance(result, str) else result
        except TypeError as exc:
            return json.dumps({"error": f"Invalid arguments: {exc}"})
        except Exception as exc:
            return json.dumps({"error": f"Tool error: {exc}"})


registry = ToolRegistry()


@registry.register(
    name="get_crew_count",
    description="Returns the number of crew members in a department.",
    parameters={
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Department name"},
        },
        "required": ["department"],
    },
)
def get_crew_count(department: str) -> dict:
    counts = {"command": 1, "science": 3, "engineering": 2, "operations": 3}
    return {"department": department, "count": counts.get(department, 0)}


@registry.register(
    name="ship_status",
    description="Returns current status of a ship system.",
    parameters={
        "type": "object",
        "properties": {
            "system": {"type": "string", "description": "System name"},
        },
        "required": ["system"],
    },
)
def ship_status(system: str) -> dict:
    systems = {
        "warp": {"system": "warp", "status": "online", "efficiency": 0.97},
        "shields": {"system": "shields", "status": "online", "efficiency": 0.85},
        "sensors": {"system": "sensors", "status": "degraded", "efficiency": 0.62},
    }
    return systems.get(system, {"system": system, "status": "unknown"})


def demo_tool_registry():
    section("Part 2: Tool Registry — Decorator Pattern")

    print("  Registered tools:")
    for tool in registry.list_tools():
        fn = tool["function"]
        print(f"    • {fn['name']}: {fn['description']}")

    print("\n  Calling tools:\n")

    result = registry.call("get_crew_count", {"department": "science"})
    print(f"    get_crew_count(science) -> {result}")

    result = registry.call("ship_status", {"system": "sensors"})
    print(f"    ship_status(sensors)    -> {result}")

    result = registry.call("unknown_tool", {})
    print(f"    unknown_tool()          -> {result}")

    result = registry.call("get_crew_count", {"wrong_param": "x"})
    print(f"    get_crew_count(bad)     -> {result}")

    print("\n  Key points:")
    print("  • Decorator keeps schema next to the handler")
    print("  • list_tools() returns OpenAI-compatible definitions")
    print("  • Unknown tools and bad arguments return errors, not crashes")


# ---------------------------------------------------------------------------
# Part 3: Safety rails — allowlist, rate limit, redaction, audit
# ---------------------------------------------------------------------------


@dataclass
class AuditEntry:
    timestamp: float
    tool_name: str
    arguments: dict
    result: str
    allowed: bool


class SafetyLayer:
    def __init__(self, allowed_tools: set[str], rate_limit: int = 10, rate_window: float = 60.0):
        self._allowed = allowed_tools
        self._rate_limit = rate_limit
        self._rate_window = rate_window
        self._call_times: list[float] = []
        self.audit_log: list[AuditEntry] = []
        self._redaction_patterns = [
            (re.compile(r"clearanceLevel[\"']?\s*[:=]\s*\d+"), "clearanceLevel: [REDACTED]"),
            (re.compile(r"api[_-]?key[\"']?\s*[:=]\s*[\"'][^\"']+[\"']", re.IGNORECASE), "api_key: [REDACTED]"),
        ]

    def check_allowed(self, tool_name: str) -> bool:
        return tool_name in self._allowed

    def check_rate_limit(self) -> bool:
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < self._rate_window]
        if len(self._call_times) >= self._rate_limit:
            return False
        self._call_times.append(now)
        return True

    def redact(self, text: str) -> str:
        for pattern, replacement in self._redaction_patterns:
            text = pattern.sub(replacement, text)
        return text

    def audit(self, tool_name: str, arguments: dict, result: str, allowed: bool):
        self.audit_log.append(AuditEntry(
            timestamp=time.time(), tool_name=tool_name,
            arguments=arguments, result=self.redact(result), allowed=allowed,
        ))


def demo_safety_rails():
    section("Part 3: Safety Rails — Defence in Depth")

    safety = SafetyLayer(
        allowed_tools={"get_crew_count", "ship_status"},
        rate_limit=3,
        rate_window=10.0,
    )

    print("  1. Allowlist:")
    print(f"     get_crew_count -> {'ALLOWED' if safety.check_allowed('get_crew_count') else 'BLOCKED'}")
    print(f"     delete_all_data -> {'ALLOWED' if safety.check_allowed('delete_all_data') else 'BLOCKED'}")

    print("\n  2. Rate limiting (max 3 calls per 10s):")
    for i in range(5):
        ok = safety.check_rate_limit()
        print(f"     Call {i + 1}: {'OK' if ok else 'BLOCKED'}")

    print("\n  3. Redaction:")
    raw = '{"name": "Voss", "clearanceLevel": 5, "api_key": "sk-secret123"}'
    print(f"     Raw:      {raw}")
    print(f"     Redacted: {safety.redact(raw)}")

    print("\n  4. Audit log:")
    safety.audit("get_crew_count", {"department": "science"}, '{"count": 3}', True)
    safety.audit("delete_all_data", {}, "", False)
    for entry in safety.audit_log:
        status = "ALLOWED" if entry.allowed else "BLOCKED"
        print(f"     [{status}] {entry.tool_name}")

    print("\n  Key points:")
    print("  • Allowlist blocks before execution — no handler runs for blocked tools")
    print("  • Rate limiter prevents runaway loops and cost explosions")
    print("  • Redaction strips secrets from logs and audit trails")
    print("  • Every call is audited — allowed or blocked")


# ---------------------------------------------------------------------------
# Part 4: Eval harness — golden tests with a mock LLM
# ---------------------------------------------------------------------------


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
    """Deterministic mock — returns pre-scripted responses in order."""

    def __init__(self, responses: list[MockLLMResponse]):
        self._responses = list(responses)
        self._call_count = 0

    def chat(self, messages: list[dict]) -> MockLLMResponse:
        if self._call_count >= len(self._responses):
            return MockLLMResponse(content="(no more scripted responses)")
        resp = self._responses[self._call_count]
        self._call_count += 1
        return resp


def run_agent_loop(llm: MockLLM, user_input: str, tool_handler) -> dict:
    messages = [
        {"role": "system", "content": "You are the Pathfinder ship AI."},
        {"role": "user", "content": user_input},
    ]
    tool_calls_made = []
    final_answer = None

    for _ in range(10):
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


def demo_eval_harness():
    section("Part 4: Eval Harness — Golden Tests (No API Calls)")

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

    print(f"  Golden case: {golden.name}")
    print(f"  User input:  '{golden.user_input}'\n")

    result = run_agent_loop(llm, golden.user_input, mock_tool_handler)
    print(f"  Tool calls made: {[tc['name'] for tc in result['tool_calls']]}")
    print(f"  Final answer:    '{result['final_answer']}'\n")

    actual_tool_names = [tc["name"] for tc in result["tool_calls"]]
    expected_tool_names = [tc["name"] for tc in golden.expected_tool_calls]

    checks = {
        "tool_names_match": actual_tool_names == expected_tool_names,
        "answer_contains_expected": golden.expected_final_answer.lower()
        in (result["final_answer"] or "").lower(),
    }

    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")

    print("\n  Key points:")
    print("  • Mock LLM — no API calls, no cost, deterministic results")
    print("  • Golden cases define expected tool calls + final answer")
    print("  • Fast enough for CI — run hundreds of cases in seconds")
    print("  • Use real API for development, mocks for regression testing")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    client = OpenAI()

    demo_message_format(client)
    pause()

    demo_tool_registry()
    pause()

    demo_safety_rails()
    pause()

    demo_eval_harness()

    print("\n" + "=" * 60)
    print("  Demo complete. Ready for exercises!")
    print("=" * 60)
