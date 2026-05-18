"""
Exercise 03 — Guarded Agent (solution)
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
# ToolRegistry (from Exercise 02 — auto-schema version)
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


SYSTEM_PROMPT = (
    "You are the DSS Pathfinder exploration AI. Use your tools to scan planets, "
    "assess habitability, and log discoveries. Be concise."
)


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
