"""
Exercise 03 — Guarded Agent
Add safety rails (allowlist, rate limiter, audit log) to the tool-calling agent.

The ToolRegistry, tool registrations, and data are provided (from Exercise 02's solution).
You only need to implement AllowList, RateLimiter, and GuardedAgent.
"""

import inspect
import json
import time
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# Type mapping (from Exercise 02)
# ---------------------------------------------------------------------------

TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

# ---------------------------------------------------------------------------
# Planetary data (from Exercise 02)
# ---------------------------------------------------------------------------

PLANET_DB = {
    "KEP-442b": {
        "name": "KEP-442b",
        "atmosphere": "nitrogen-oxygen",
        "gravity": 1.3,
        "hazards": ["seismic activity"],
        "distance_ly": 1206,
    },
    "PROX-b": {
        "name": "PROX-b",
        "atmosphere": "carbon-dioxide",
        "gravity": 1.1,
        "hazards": ["radiation"],
        "distance_ly": 4.2,
    },
    "TRAP-1e": {
        "name": "TRAP-1e",
        "atmosphere": "nitrogen-oxygen",
        "gravity": 0.9,
        "hazards": [],
        "distance_ly": 39,
    },
}

MISSION_LOG: list[dict] = []

# ---------------------------------------------------------------------------
# ToolRegistry (from Exercise 02 — already implemented)
# ---------------------------------------------------------------------------


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, description: str):
        def decorator(fn: Callable) -> Callable:
            sig = inspect.signature(fn)
            properties: dict[str, dict] = {}
            required: list[str] = []

            for param_name, param in sig.parameters.items():
                json_type = TYPE_MAP.get(param.annotation, "string")
                properties[param_name] = {"type": json_type}
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            self._tools[fn.__name__] = {
                "name": fn.__name__,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
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
# Register planetary tools (from Exercise 02)
# ---------------------------------------------------------------------------

registry = ToolRegistry()


@registry.register("Scan a planet by its catalog ID and return its data.")
def scan_planet(planet_id: str) -> str:
    planet = PLANET_DB.get(planet_id)
    if planet is None:
        return json.dumps({"error": f"Unknown planet: {planet_id}"})
    return json.dumps(planet)


@registry.register("Check habitability given an atmosphere type and surface gravity.")
def check_habitability(atmosphere: str, gravity: float) -> str:
    score = 0.0
    if atmosphere == "nitrogen-oxygen":
        score += 50.0
    elif atmosphere == "nitrogen-argon":
        score += 20.0
    if 0.8 <= gravity <= 1.2:
        score += 50.0
    elif 0.5 <= gravity <= 1.5:
        score += 25.0
    return json.dumps({"atmosphere": atmosphere, "gravity": gravity, "habitability_score": score})


@registry.register("Log a discovery to the mission log.")
def log_discovery(planet_id: str, summary: str) -> str:
    entry = {"planet_id": planet_id, "summary": summary}
    MISSION_LOG.append(entry)
    return json.dumps({"status": "logged", "entry": entry})


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

SYSTEM_PROMPT = (
    "You are the DSS Pathfinder exploration AI. Use your tools to scan planets, "
    "assess habitability, and log discoveries. Be concise."
)


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
    allow_list = AllowList(permitted={"scan_planet", "check_habitability"})
    rate_limiter = RateLimiter(max_calls=10, window_seconds=60.0)
    agent = GuardedAgent(client, registry, allow_list, rate_limiter)

    print("DSS Pathfinder Guarded Agent ready. Type a question (or 'quit').")
    print("Allowed tools: scan_planet, check_habitability")
    print("Blocked tool:  log_discovery (try asking to log a discovery!)\n")

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
