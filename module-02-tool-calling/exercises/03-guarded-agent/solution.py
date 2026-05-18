"""
Exercise 03 — Guarded Agent (solution)
"""

import json
import time
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Ship data
# ---------------------------------------------------------------------------

CREW_DATA = {
    "command": [{"name": "Commander Elara Voss", "role": "Captain"}],
    "science": [
        {"name": "Dr. Jian Chen", "role": "Chief Science Officer"},
        {"name": "Ensign Dax Morel", "role": "Xenobiologist"},
        {"name": "Lt. Priya Sharma", "role": "Astrophysicist"},
    ],
    "engineering": [
        {"name": "Chief Engineer Mira Chen", "role": "Lead Engineer"},
        {"name": "Specialist Bodhi Kwan", "role": "Systems Tech"},
    ],
    "medical": [{"name": "Dr. Amara Osei", "role": "Chief Medical Officer"}],
}

SHIP_SYSTEMS = {
    "warp": {"system": "warp", "status": "online", "efficiency": 0.97},
    "shields": {"system": "shields", "status": "online", "efficiency": 0.85},
    "sensors": {"system": "sensors", "status": "degraded", "efficiency": 0.62},
    "life_support": {"system": "life_support", "status": "online", "efficiency": 0.99},
}


# ---------------------------------------------------------------------------
# ToolRegistry (from Exercise 02)
# ---------------------------------------------------------------------------

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict):
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "handler": fn,
            }
            return fn
        return decorator

    def list_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = self._tools[name]["handler"](**arguments)
            return result if isinstance(result, str) else json.dumps(result)
        except Exception as exc:
            return json.dumps({"error": f"Tool error: {exc}"})


# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------

registry = ToolRegistry()


@registry.register("get_crew_count", "Get the number of crew members in a department.", {
    "type": "object",
    "properties": {
        "department": {"type": "string", "description": "Department name"},
    },
    "required": ["department"],
})
def get_crew_count(department: str) -> str:
    crew = CREW_DATA.get(department, [])
    return json.dumps({"department": department, "count": len(crew)})


@registry.register("get_ship_status", "Get the current status of a ship system.", {
    "type": "object",
    "properties": {
        "system": {"type": "string", "description": "System name"},
    },
    "required": ["system"],
})
def get_ship_status(system: str) -> str:
    status = SHIP_SYSTEMS.get(system, {"system": system, "status": "unknown"})
    return json.dumps(status)


@registry.register("search_crew", "Search crew members by name or role.", {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search term"},
    },
    "required": ["query"],
})
def search_crew(query: str) -> str:
    matches = []
    q = query.lower()
    for dept, members in CREW_DATA.items():
        for member in members:
            if q in member["name"].lower() or q in member["role"].lower():
                matches.append({**member, "department": dept})
    return json.dumps(matches)


# ---------------------------------------------------------------------------
# Safety classes
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    timestamp: float
    tool_name: str
    arguments: dict
    allowed: bool
    result: str | None = None


class AllowList:
    def __init__(self, permitted: set[str]):
        self._permitted = permitted

    def check(self, name: str) -> bool:
        return name in self._permitted


@dataclass
class RateLimiter:
    max_calls: int
    window_seconds: float
    _timestamps: list[float] = field(default_factory=list)

    def allow(self) -> bool:
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < self.window_seconds]
        if len(self._timestamps) >= self.max_calls:
            return False
        self._timestamps.append(now)
        return True


# ---------------------------------------------------------------------------
# Guarded agent
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    final_answer: str | None
    tool_calls_made: list[str] = field(default_factory=list)
    steps: int = 0
    audit_log: list[AuditEntry] = field(default_factory=list)


SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Use your tools to answer crew and ship queries. Be concise."


class GuardedAgent:
    def __init__(
        self,
        client,
        tool_registry: ToolRegistry,
        allow_list: AllowList,
        rate_limiter: RateLimiter,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.client = client
        self.registry = tool_registry
        self.allow_list = allow_list
        self.rate_limiter = rate_limiter
        self.system_prompt = system_prompt

    @staticmethod
    def _build_tool_error(tc_id: str, reason: str) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tc_id,
            "content": json.dumps({"error": reason}),
        }

    def _handle_tool_call(self, tc, messages) -> AuditEntry:
        name = tc.function.name
        args = json.loads(tc.function.arguments)

        if not self.allow_list.check(name):
            msg = self._build_tool_error(tc.id, f"Tool not permitted: {name}")
            messages.append(msg)
            return AuditEntry(
                timestamp=time.time(), tool_name=name, arguments=args,
                allowed=False, result=msg["content"],
            )

        if not self.rate_limiter.allow():
            msg = self._build_tool_error(tc.id, "Rate limit exceeded")
            messages.append(msg)
            return AuditEntry(
                timestamp=time.time(), tool_name=name, arguments=args,
                allowed=False, result=msg["content"],
            )

        result = self.registry.execute(name, args)
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        return AuditEntry(
            timestamp=time.time(), tool_name=name, arguments=args,
            allowed=True, result=result,
        )

    def run(self, question: str, max_steps: int = 5) -> AgentResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question},
        ]
        tool_calls_made: list[str] = []
        audit_log: list[AuditEntry] = []
        steps = 0

        for _ in range(max_steps):
            steps += 1
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self.registry.list_tools(),
            )
            message = response.choices[0].message

            if message.tool_calls:
                messages.append(message)
                for tc in message.tool_calls:
                    tool_calls_made.append(tc.function.name)
                    audit_log.append(self._handle_tool_call(tc, messages))
            elif message.content:
                return AgentResult(
                    final_answer=message.content,
                    tool_calls_made=tool_calls_made,
                    steps=steps,
                    audit_log=audit_log,
                )
            else:
                break

        return AgentResult(
            final_answer=None,
            tool_calls_made=tool_calls_made,
            steps=steps,
            audit_log=audit_log,
        )


# ---------------------------------------------------------------------------
# CLI chat loop
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI()
    allow_list = AllowList(permitted={"get_crew_count", "get_ship_status"})
    rate_limiter = RateLimiter(max_calls=10, window_seconds=60.0)
    agent = GuardedAgent(client, registry, allow_list, rate_limiter)

    print("DSS Pathfinder Guarded Agent ready. Type a question (or 'quit').")
    print("Allowed tools: get_crew_count, get_ship_status")
    print("Blocked tool:  search_crew (try asking to find someone!)\n")

    while True:
        q = input("You: ").strip()
        if not q or q.lower() in ("quit", "exit"):
            break
        result = agent.run(q)
        print(f"\nAgent: {result.final_answer}")
        if result.tool_calls_made:
            print(f"  (tools used: {', '.join(result.tool_calls_made)})")
        if result.audit_log:
            print("  Audit log:")
            for entry in result.audit_log:
                status = "ALLOWED" if entry.allowed else "BLOCKED"
                print(f"    [{status}] {entry.tool_name}({json.dumps(entry.arguments)})")
        print()
