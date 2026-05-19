"""
Module 2 Demo — Tool Calling
Run:  python module-02-tool-calling/demo/demo.py

Walks through the full module in one script:
  Part 1: Tool-call message flow — live tool call, trace the 4 message roles
  Part 2: Tool registry — live agent with decorator-registered tools
  Part 3: Guarded agent — safety rails (allowlist, rate limit, redaction, audit) wrapping the agent

Requires: OPENAI_API_KEY environment variable.
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


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
    section("Part 1: Tool-Call Message Flow — The 4 Roles")

    print("  Chat with the Pathfinder AI. It has one tool: query_crew.")
    print("  Watch the message flow: SYSTEM → USER → ASSISTANT (tool_call) → TOOL → ASSISTANT")
    print("  Type 'quit' to return to the menu.\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. You have access to a query_crew tool "
                "for looking up crew assigned to missions. Always cite the data source."
            ),
        },
    ]

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        print(f"  [USER]      {user_msg}")

        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        assistant_msg = response.choices[0].message

        if assistant_msg.tool_calls:
            messages.append(assistant_msg)
            for tc in assistant_msg.tool_calls:
                args = json.loads(tc.function.arguments)
                print(f"  [ASSISTANT] tool_call → {tc.function.name}({tc.function.arguments})")
                result = execute_tool(tc.function.name, args)
                print(f"  [TOOL]      {tc.function.name} returned: {result[:120]}")
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )

            final = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS
            )
            answer = final.choices[0].message.content
            messages.append({"role": "assistant", "content": answer})
            print(f"  [ASSISTANT] {answer}\n")
        else:
            content = assistant_msg.content
            messages.append({"role": "assistant", "content": content})
            print(f"  [ASSISTANT] {content}\n")

    print("  Key concepts:")
    print("  • 4 message roles: system, user, assistant, tool")
    print("  • The model decides whether to call a tool or answer directly")
    print("  • Tool results feed back as messages — the model interprets them")
    print("  • This request-response loop is the foundation of every agent")


# ---------------------------------------------------------------------------
# Shared: live agent loop (used by Parts 2 and 3)
# ---------------------------------------------------------------------------


def agent_loop(client: OpenAI, messages: list[dict], tools_list: list[dict],
               tool_handler, *, label: str = ""):
    """One turn of the agent loop: call LLM, handle tool calls, return final answer."""
    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=tools_list
    )
    assistant_msg = response.choices[0].message

    if not assistant_msg.tool_calls:
        messages.append({"role": "assistant", "content": assistant_msg.content})
        print(f"  [ASSISTANT] {assistant_msg.content}\n")
        return

    messages.append(assistant_msg)
    for tc in assistant_msg.tool_calls:
        args = json.loads(tc.function.arguments)
        print(f"  [ASSISTANT] tool_call → {tc.function.name}({tc.function.arguments})")
        result, allowed = tool_handler(tc.function.name, args)
        tag = "ALLOWED" if allowed else "BLOCKED"
        print(f"  [{tag}]     {tc.function.name} → {result[:120]}")
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    final = client.chat.completions.create(
        model=MODEL, messages=messages, tools=tools_list
    )
    answer = final.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    print(f"  [ASSISTANT] {answer}\n")


# ---------------------------------------------------------------------------
# Part 2: Tool registry — decorator pattern, live agent
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


def demo_tool_registry(client: OpenAI):
    section("Part 2: Tool Registry — Live Agent with Decorator-Registered Tools")

    print("  Registered tools (via @registry.register decorator):")
    for tool in registry.list_tools():
        fn = tool["function"]
        params = ", ".join(fn["parameters"].get("required", []))
        print(f"    • {fn['name']}({params}) — {fn['description']}")

    print("\n  Chat with the agent. The LLM picks which tool to call;")
    print("  the registry dispatches to the right handler.")
    print("  Type 'quit' to return to the menu.\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. Use get_crew_count to look up "
                "department headcounts and ship_status to check system health. "
                "Always report exact numbers from the tools."
            ),
        },
    ]

    def handle_via_registry(name: str, arguments: dict) -> tuple[str, bool]:
        result = registry.call(name, arguments)
        return result, True

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        print(f"  [USER]      {user_msg}")
        agent_loop(client, messages, registry.list_tools(), handle_via_registry)

    print("  Key concepts:")
    print("  • @registry.register() decorator — schema lives next to the handler")
    print("  • list_tools() returns OpenAI-compatible function definitions")
    print("  • call() dispatches by name with argument validation")
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
    def __init__(self, allowed_tools: set[str], rate_limit: int = 3, rate_window: float = 60.0):
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


def demo_safety_rails(client: OpenAI):
    section("Part 3: Guarded Agent — Safety Rails Wrapping the Tool Registry")

    safety = SafetyLayer(
        allowed_tools={"get_crew_count", "ship_status"},
        rate_limit=2,
        rate_window=60.0,
    )

    print("  Same agent as Part 2, but every tool call now passes through:")
    print("    1. Allowlist    — only {get_crew_count, ship_status} permitted")
    print("    2. Rate limiter — max 2 calls per 60s sliding window")
    print("    3. Redaction    — strips clearanceLevel, api_key from output")
    print("    4. Audit log    — every call recorded (allowed or blocked)")
    print()
    print("  Chat normally. Try asking fast to hit the rate limit.")
    print("  Type 'audit' to view the log, 'quit' to return.\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. Use get_crew_count to look up "
                "department headcounts and ship_status to check system health. "
                "Always report exact numbers from the tools."
            ),
        },
    ]

    def handle_guarded(name: str, arguments: dict) -> tuple[str, bool]:
        if not safety.check_allowed(name):
            result = json.dumps({"error": f"Tool '{name}' is not on the allowlist"})
            safety.audit(name, arguments, result, False)
            return result, False

        if not safety.check_rate_limit():
            result = json.dumps({"error": "Rate limit exceeded"})
            safety.audit(name, arguments, result, False)
            return result, False

        result = registry.call(name, arguments)
        safety.audit(name, arguments, result, True)
        return safety.redact(result), True

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        if user_msg.lower() == "audit":
            if not safety.audit_log:
                print("  (audit log is empty)\n")
            else:
                print(f"  Audit log ({len(safety.audit_log)} entries):")
                for entry in safety.audit_log:
                    status = "ALLOWED" if entry.allowed else "BLOCKED"
                    print(f"    [{status}] {entry.tool_name}({entry.arguments}) → {entry.result[:80]}")
                print()
            continue

        messages.append({"role": "user", "content": user_msg})
        print(f"  [USER]      {user_msg}")
        agent_loop(client, messages, registry.list_tools(), handle_guarded)

    print("  Key concepts:")
    print("  • Allowlist — blocks disallowed tools before execution")
    print("  • Rate limiter — sliding window prevents runaway loops and cost spikes")
    print("  • Redaction — strips sensitive data from output before logging")
    print("  • Audit log — immutable record of every call, allowed or blocked")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


DEMOS = {
    "1": ("Tool-call message flow",                         demo_message_format),
    "2": ("Tool registry — live agent, decorator dispatch", demo_tool_registry),
    "3": ("Guarded agent — safety rails wrapping the registry", demo_safety_rails),
}


if __name__ == "__main__":
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 2 DEMO — TOOL CALLING")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print(f"  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            fn(client)
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. Message flow   — system → user → assistant (tool_call) → tool → assistant")
    print("  2. Tool registry  — @register decorator, schema + handler in one place")
    print("  3. Guarded agent  — allowlist, rate limiter, redaction, audit log")
    print()
    print("=" * 60)
