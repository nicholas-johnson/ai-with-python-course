"""
Exercise 03 — Guarded Agent
Add safety rails (allowlist, rate limiter, audit log) to the tool-calling agent.

The ToolRegistry, tool registrations, and data are provided (from Exercise 02's solution).
You only need to implement AllowList, RateLimiter, and GuardedAgent.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Ship data (same as exercises 01/02)
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
# ToolRegistry (from Exercise 02 — already implemented)
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
# Register tools (from Exercise 02)
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
# Safety classes — YOUR CODE HERE
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    timestamp: float
    tool_name: str
    arguments: dict
    allowed: bool
    result: str | None = None


class AllowList:
    """Check whether a tool name is in the permitted set."""

    def __init__(self, permitted: set[str]):
        self._permitted = permitted

    def check(self, name: str) -> bool:
        """Return True if the tool is allowed, False otherwise."""
        # TODO: implement
        pass


@dataclass
class RateLimiter:
    """Sliding-window rate limiter."""

    max_calls: int
    window_seconds: float
    _timestamps: list[float] = field(default_factory=list)

    def allow(self) -> bool:
        """
        Return True if a new call is within the rate limit.
        Prune timestamps outside the window, then check count.
        If allowed, record the current timestamp.
        """
        # TODO: implement sliding-window rate limiting
        pass


# ---------------------------------------------------------------------------
# Guarded agent result
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    final_answer: str | None
    tool_calls_made: list[str] = field(default_factory=list)
    steps: int = 0
    audit_log: list[AuditEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# GuardedAgent — YOUR CODE HERE
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Use your tools to answer crew and ship queries. Be concise."


class GuardedAgent:
    """
    A tool-calling agent with safety rails.

    Before executing each tool call:
    1. Check the AllowList — if blocked, send back an error message as the tool result
       (so the model knows the tool was denied and can try something else).
    2. Check the RateLimiter — if exceeded, send back a rate-limit error message.
    3. Log every call (allowed or blocked) to the audit log.
    """

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
        """Build a tool-role message dict containing a JSON error.

        Return format:
            {"role": "tool", "tool_call_id": tc_id,
             "content": '{"error": "<reason>"}'}
        """
        # TODO: implement
        raise NotImplementedError

    def _handle_tool_call(self, tc, messages) -> AuditEntry:
        """Process one tool call: check allowlist, check rate limit, execute or deny.

        Steps:
        1. If the tool is not on the allow list → append _build_tool_error
           and return an AuditEntry with allowed=False.
        2. Else if the rate limiter denies → same pattern.
        3. Otherwise execute via self.registry.execute(), append the
           tool result message, and return an AuditEntry with allowed=True.
        """
        # TODO: implement
        raise NotImplementedError

    def run(self, question: str, max_steps: int = 5) -> AgentResult:
        """
        Run the guarded agent loop.

        Uses _handle_tool_call for each tool call in the response.
        Collects AuditEntry objects and tool names across iterations.
        Returns an AgentResult when the model produces text or max_steps is hit.
        """
        # TODO: implement the guarded agent loop
        raise NotImplementedError


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
