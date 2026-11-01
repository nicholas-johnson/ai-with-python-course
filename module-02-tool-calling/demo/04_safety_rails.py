"""Part 4: Guarded agent — allowlist, rate limit, redaction, audit."""

import json
import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def agent_loop(client: OpenAI, messages: list[dict], tools_list: list[dict], tool_handler):
    """One turn: call the model, run any tool calls, print the answer."""
    response = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages, tools=tools_list
    )
    calls = [item for item in response.output if item.type == "function_call"]

    if not calls:
        messages.append({"role": "assistant", "content": response.output_text})
        print(f"  [ASSISTANT] {response.output_text}\n")
        return

    messages += response.output
    for tc in calls:
        args = json.loads(tc.arguments)
        print(f"  [FUNCTION_CALL] {tc.name}({tc.arguments})")
        result, allowed = tool_handler(tc.name, args)
        tag = "ALLOWED" if allowed else "BLOCKED"
        print(f"  [{tag}]     {tc.name} → {result[:120]}")
        messages.append({"type": "function_call_output", "call_id": tc.call_id, "output": result})

    final = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages, tools=tools_list
    )
    answer = final.output_text
    messages.append({"role": "assistant", "content": answer})
    print(f"  [ASSISTANT] {answer}\n")


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
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
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
            (
                re.compile(r"api[_-]?key[\"']?\s*[:=]\s*[\"'][^\"']+[\"']", re.IGNORECASE),
                "api_key: [REDACTED]",
            ),
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
    print("=" * 60)
    print("PART 4: GUARDED AGENT")
    print("=" * 60)
    print()

    safety = SafetyLayer(
        allowed_tools={"get_crew_count", "ship_status"},
        rate_limit=2,
        rate_window=60.0,
    )

    print("  Same agent as Part 3, but every tool call now passes through:")
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
                    preview = entry.result[:80]
                    print(f"    [{status}] {entry.tool_name}({entry.arguments}) → {preview}")
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
